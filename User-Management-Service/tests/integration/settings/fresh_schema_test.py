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


def assert_schema(connection: Connection) -> None:
    inspector = inspect(connection)
    assert set(inspector.get_table_names()) == {"users", "alembic_version"}
    columns = {column["name"]: column for column in inspector.get_columns("users")}
    assert set(columns) == {
        "id",
        "name",
        "surname",
        "username",
        "password_hash",
        "email",
        "phone_number",
        "image_s3_path",
        "created_at",
        "updated_at",
    }
    for name in (
        "id",
        "name",
        "surname",
        "username",
        "password_hash",
        "email",
        "created_at",
    ):
        assert columns[name]["nullable"] is False
    for name in ("phone_number", "image_s3_path", "updated_at"):
        assert columns[name]["nullable"] is True
    assert inspector.get_pk_constraint("users")["constrained_columns"] == ["id"]
    assert not inspector.get_foreign_keys("users")
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
        assert restored.updated_at is None and restored.image_s3_path is None
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
    assert len(revisions) == 1 and revisions[0].down_revision is None
    entry = Path("scripts/entry.sh").read_text()
    assert "alembic upgrade head" in entry and 'exec "$@"' in entry
    assert "super" not in entry.lower()
    assert "super" not in Path(".env.example").read_text().lower()
