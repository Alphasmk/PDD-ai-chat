from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text, inspect, update
from sqlalchemy.orm import selectinload
from httpx import AsyncClient
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from source.infrastructure.database.models import Role, User
from tests.integration.conftest import seeded_account


async def test_catalog_has_two_roles_and_user_foreign_key(engine: AsyncEngine) -> None:
    async with AsyncSession(engine) as session:
        roles = (await session.execute(select(Role).order_by(Role.id))).scalars().all()
        assert [(role.id, role.value, role.label) for role in roles] == [
            (1, "user", "Пользователь"),
            (2, "admin", "Администратор"),
        ]
    async with engine.connect() as connection:

        def check_foreign_key(sync_connection: Connection) -> None:
            foreign_keys = inspect(sync_connection).get_foreign_keys("users")
            assert any(
                item["constrained_columns"] == ["role_id"]
                and item["referred_table"] == "roles"
                for item in foreign_keys
            )

        await connection.run_sync(check_foreign_key)


async def test_third_role_is_rejected(engine: AsyncEngine) -> None:
    async with AsyncSession(engine) as session:
        session.add(Role(id=3, value="superadmin", label="Суперадминистратор"))
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()


def migrate_preserved_accounts(connection: Connection) -> None:
    config = Config("alembic.ini")
    config.attributes["connection"] = connection
    command.downgrade(config, "users_roles_20260927")
    for index, role in enumerate(("user", "admin", "superadmin")):
        connection.execute(
            text(
                "INSERT INTO users (id, name, surname, username, password_hash, email, role, is_blocked, phone_number, created_at, updated_at) "
                "VALUES (:id, 'Alice', 'Smith', :username, :hash, :email, :role, :blocked, :phone, '2026-01-01 00:00:00', '2026-02-01 00:00:00')"
            ),
            {
                "id": str(uuid4())
                if connection.dialect.name == "postgresql"
                else uuid4().hex,
                "username": f"previous{index}",
                "email": f"previous{index}@example.com",
                "hash": f"preserved_hash_{index}",
                "role": role,
                "blocked": index == 0,
                "phone": f"+1202555010{index}",
            },
        )
    profile_query = text(
        "SELECT id, name, surname, username, password_hash, email, phone_number, created_at, updated_at, is_blocked FROM users ORDER BY username"
    )
    before = connection.execute(profile_query).all()
    command.upgrade(config, "head")
    assert connection.execute(profile_query).all() == before
    command.downgrade(config, "users_roles_20260927")
    assert connection.execute(
        text("SELECT role FROM users ORDER BY username")
    ).scalars().all() == ["user", "admin", "superadmin"]
    assert connection.execute(profile_query).all() == before
    command.upgrade(config, "head")
    assert connection.execute(profile_query).all() == before


async def test_migration_preserves_profiles_hashes_and_protected_admin(
    engine: AsyncEngine,
) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(migrate_preserved_accounts)
    async with AsyncSession(engine) as session:
        users = (
            (await session.execute(select(User).order_by(User.username)))
            .scalars()
            .all()
        )
        assert [
            (user.username, user.password_hash, user.role_id, user.is_superadmin)
            for user in users
        ] == [
            ("previous0", "preserved_hash_0", 1, False),
            ("previous1", "preserved_hash_1", 2, False),
            ("previous2", "preserved_hash_2", 2, True),
        ]
        assert all(user.name == "Alice" and user.surname == "Smith" for user in users)
        assert [user.is_blocked for user in users] == [True, False, False]


async def test_roles_endpoint_reads_catalog_and_user_relationship(
    engine: AsyncEngine, client: AsyncClient
) -> None:
    user = await seeded_account(client, engine, "reader")
    async with AsyncSession(engine) as session:
        stored = (
            await session.execute(select(User).options(selectinload(User.role)))
        ).scalar_one()
        assert stored.role.id == stored.role_id == 1
        assert stored.role.value == "user"
        await session.execute(
            update(Role).where(Role.id == 1).values(label="Обычный пользователь")
        )
        await session.commit()
    response = await client.get("/api/v1/roles", headers=user.headers)
    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"value": "user", "label": "Обычный пользователь"},
            {"value": "admin", "label": "Администратор"},
        ]
    }
