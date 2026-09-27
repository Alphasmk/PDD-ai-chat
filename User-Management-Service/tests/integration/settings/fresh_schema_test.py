from datetime import timezone
from pathlib import Path
from uuid import UUID
from httpx import AsyncClient
from sqlalchemy import inspect, select, func
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from alembic.config import Config
from alembic.script import ScriptDirectory
from source.infrastructure.database.models import User
from source.infrastructure.database.user_repository import UserRepository
from source.domain.value_objects import ID
from tests.integration.conftest import account
import pytest
from sqlalchemy.exc import IntegrityError
from uuid import uuid4


def assert_schema(connection: Connection) -> None:
    inspector = inspect(connection)
    assert set(inspector.get_table_names()) == {"users", "roles", "alembic_version"}
    columns = {column["name"]: column for column in inspector.get_columns("users")}
    assert set(columns) == {
        "id",
        "name",
        "surname",
        "username",
        "password_hash",
        "email",
        "phone_number",
        "created_at",
        "updated_at",
        "role_id",
        "is_blocked",
        "is_superadmin",
    }
    for name in (
        "id",
        "name",
        "surname",
        "username",
        "password_hash",
        "email",
        "created_at",
        "role_id",
        "is_blocked",
        "is_superadmin",
    ):
        assert columns[name]["nullable"] is False
    for name in ("phone_number", "updated_at"):
        assert columns[name]["nullable"] is True
    assert inspector.get_pk_constraint("users")["constrained_columns"] == ["id"]
    assert inspector.get_foreign_keys("users")[0]["referred_table"] == "roles"
    unique = {
        tuple(item["column_names"])
        for item in inspector.get_unique_constraints("users")
    }
    assert {("email",), ("phone_number",)} <= unique
    indexes = inspector.get_indexes("users")
    assert any(
        item["name"] == "ix_users_username"
        and item["unique"]
        and item["column_names"] == ["username"]
        for item in indexes
    )


async def test_fresh_schema_zero_users_and_first_signup(
    engine: AsyncEngine, client: AsyncClient
) -> None:
    async with engine.connect() as connection:
        await connection.run_sync(assert_schema)
    async with AsyncSession(engine) as db:
        assert await db.scalar(select(func.count()).select_from(User)) == 0
    user = await account(client)
    async with AsyncSession(engine) as db:
        assert await db.scalar(select(func.count()).select_from(User)) == 1
        restored = await UserRepository(db).get_by_id(ID(UUID(user.id)))
        assert restored is not None
        assert restored.created_at.tzinfo == timezone.utc
        assert restored.updated_at is None
        assert (await UserRepository(db).get_by_username("alice")) == restored
        await client.patch(
            "/api/v1/users/me", headers=user.headers, json={"name": "Jane"}
        )
        await db.refresh(await db.get_one(User, UUID(user.id)))
        updated = await UserRepository(db).get_by_id(ID(UUID(user.id)))
        assert (
            updated is not None
            and updated.name.value == "Jane"
            and updated.updated_at is not None
        )
        assert updated.updated_at.tzinfo == timezone.utc
        assert updated.created_at == restored.created_at


def test_single_baseline_no_bootstrap() -> None:
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    revisions = list(scripts.walk_revisions())
    assert len(revisions) == 2 and revisions[-1].down_revision is None
    assert revisions[0].down_revision == "users_roles_20260927"
    assert scripts.get_heads() == ["role_catalog_20260927"]
    entry = Path("scripts/entry.sh").read_text()
    assert "python -m scripts.initialize_service" in entry and 'exec "$@"' in entry


@pytest.mark.parametrize(
    "role_id, blocked, protected",
    [(3, False, False), (2, True, False), (1, False, True), (2, True, True)],
)
async def test_invalid_storage_state(
    engine: AsyncEngine, role_id: int, blocked: bool, protected: bool
) -> None:
    async with AsyncSession(engine) as session:
        session.add(
            User(
                id=uuid4(),
                name="Alice",
                surname="Smith",
                username="invalid",
                email="invalid@example.com",
                password_hash="test",
                role_id=role_id,
                is_superadmin=protected,
                is_blocked=blocked,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()


async def test_single_superadmin_constraint(engine: AsyncEngine) -> None:
    async with AsyncSession(engine) as session:
        for index in range(2):
            session.add(
                User(
                    id=uuid4(),
                    name="Alice",
                    surname="Smith",
                    username=f"owner{index}",
                    email=f"owner{index}@example.com",
                    password_hash="test",
                    role_id=2,
                    is_superadmin=True,
                    is_blocked=False,
                )
            )
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()
