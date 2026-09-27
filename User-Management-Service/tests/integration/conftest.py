"""HTTP tests use a fresh migrated database and isolated publisher/cache/token ports."""

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import AsyncClient, ASGITransport, Response
from sqlalchemy import text, update
from source.domain.value_objects.user_role import UserRole
from source.infrastructure.database.models import User
from uuid import UUID
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from source.main import app
from source.infrastructure.jwt import TokenProvider
from source.presentation.api.dependencies.adapters import (
    get_session,
    get_token_service,
    get_message_broker_service,
    get_cache_service,
)
from tests.adapters.broker_service import FakeMessageService
from tests.adapters.cache_service import FakeRedisTokenBlacklist


def apply_baseline(connection: Connection) -> None:
    config = Config("alembic.ini")
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


@pytest_asyncio.fixture
async def engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    postgres_url = os.environ.get("UMS_TEST_POSTGRES_URL")
    if os.environ.get("UMS_REQUIRE_POSTGRES") == "1" and not postgres_url:
        pytest.fail("UMS_REQUIRE_POSTGRES=1 requires an isolated UMS_TEST_POSTGRES_URL")
    schema = "ums_test_" + uuid4().hex
    admin: AsyncEngine | None = None
    if postgres_url:
        if not postgres_url.startswith("postgresql+asyncpg://"):
            raise ValueError("UMS_TEST_POSTGRES_URL must use postgresql+asyncpg")
        admin = create_async_engine(postgres_url)
        async with admin.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        database = create_async_engine(
            postgres_url, connect_args={"server_settings": {"search_path": schema}}
        )
    else:
        database = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'users.db'}")
    try:
        async with database.begin() as connection:
            await connection.run_sync(apply_baseline)
        yield database
    finally:
        await database.dispose()
        if admin is not None:
            async with admin.begin() as connection:
                await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            await admin.dispose()


@pytest.fixture
def publisher() -> FakeMessageService:
    return FakeMessageService()


@pytest.fixture
def blacklist() -> FakeRedisTokenBlacklist:
    return FakeRedisTokenBlacklist()


@pytest.fixture
def provider() -> TokenProvider:
    return TokenProvider("isolated-http-test-secret-32-characters", "HS256", 15, 7)


@pytest_asyncio.fixture
async def client(
    engine: AsyncEngine,
    publisher: FakeMessageService,
    blacklist: FakeRedisTokenBlacklist,
    provider: TokenProvider,
) -> AsyncIterator[AsyncClient]:
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def session() -> AsyncIterator[AsyncSession]:
        async with maker() as db:
            try:
                yield db
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    app.dependency_overrides[get_session] = session
    app.dependency_overrides[get_message_broker_service] = lambda: publisher
    app.dependency_overrides[get_cache_service] = lambda: blacklist
    app.dependency_overrides[get_token_service] = lambda: provider
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as http:
            yield http
    finally:
        app.dependency_overrides.clear()


def response_data(response: Response) -> dict[str, object]:
    raw: object = response.json()
    assert isinstance(raw, dict)
    result: dict[str, object] = {}
    for key, value in raw.items():
        assert isinstance(key, str)
        result[key] = value
    return result


def json_string(response: Response, key: str) -> str:
    value = response_data(response)[key]
    assert isinstance(value, str)
    return value


def signup_payload(username: str = "alice") -> dict[str, str]:
    return {
        "name": "Alice",
        "surname": "Smith",
        "username": username,
        "password": "Test1234",
        "email": f"{username}@example.com",
    }


@dataclass(frozen=True)
class Account:
    id: str
    username: str
    access: str
    refresh: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access}"}


async def account(client: AsyncClient, username: str = "alice") -> Account:
    signup = await client.post("/api/v1/auth/signup", json=signup_payload(username))
    assert signup.status_code == 201, signup.text
    login = await client.post(
        "/api/v1/auth/login", data={"username": username, "password": "Test1234"}
    )
    assert login.status_code == 200, login.text
    return Account(
        json_string(signup, "id"),
        username,
        json_string(login, "access_token"),
        json_string(login, "refresh_token"),
    )


async def seeded_account(
    client: AsyncClient,
    engine: AsyncEngine,
    username: str,
    role: UserRole = UserRole.USER,
    is_superadmin: bool = False,
) -> Account:
    result = await account(client, username)
    async with AsyncSession(engine) as session:
        await session.execute(
            update(User)
            .where(User.id == UUID(result.id))
            .values(role_id=role.storage_id, is_superadmin=is_superadmin)
        )
        await session.commit()
    return result
