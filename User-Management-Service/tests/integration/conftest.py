import pytest
import pytest_asyncio
import logging
from httpx import AsyncClient, ASGITransport
from alembic import command
from alembic.config import Config
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from source.main import app
from source.infrastructure.database.session import DatabaseSessionmaker, get_database
from source.infrastructure.cache import get_cache_database
from source.infrastructure.cache.session import CacheSessionmaker
from source.infrastructure.message_broker import BrokerHandler
from source.presentation.api.dependencies import get_session, get_redis_session
from source.presentation.api.schemas.auth import UserSignupRequest
from source.domain.value_objects import ID
from source.domain.enums.user_role import UserRole
from source.infrastructure.database.models import User
from tests.integration.settings.test_config import get_test_settings


@pytest.fixture(scope="session", autouse=True)
def auto_run_migrations():
    settings = get_test_settings()
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.database.postgres_url))
    command.upgrade(alembic_cfg, "head")
    yield


@pytest_asyncio.fixture(scope="function")
async def test_db_maker():
    settings = get_test_settings()
    logging.debug(settings)
    test_db_url = str(settings.database.postgres_url)

    test_db_sessionmaker = DatabaseSessionmaker()
    await test_db_sessionmaker.init_db(test_db_url)

    app.dependency_overrides[get_database] = lambda: test_db_sessionmaker

    try:
        yield test_db_sessionmaker
    except Exception as e:
        logging.error(f"Error when connecting to test Postgres database: {str(e)}")
        raise
    finally:
        await test_db_sessionmaker.close()
        if get_database in app.dependency_overrides:
            del app.dependency_overrides[get_database]


@pytest_asyncio.fixture(scope="function")
async def test_cache_maker():
    settings = get_test_settings()
    test_cache_url = str(settings.cache.redis_url)

    test_cache_sessionmaker = CacheSessionmaker()
    await test_cache_sessionmaker.init_db(test_cache_url)

    app.dependency_overrides[get_cache_database] = lambda: test_cache_sessionmaker

    try:
        yield test_cache_sessionmaker
    except Exception as e:
        logging.error(f"Error when connecting to test Redis database: {str(e)}")
        raise
    finally:
        await test_cache_sessionmaker.close()
        if get_cache_database in app.dependency_overrides:
            del app.dependency_overrides[get_cache_database]


@pytest_asyncio.fixture(scope="function", autouse=True)
async def test_broker_maker():
    settings = get_test_settings()
    test_broker_url = str(settings.broker.rabbit_url)

    test_broker_sessionmaker = BrokerHandler(test_broker_url)
    await test_broker_sessionmaker.connect()
    old_connection = getattr(app.state, "broker", None)
    app.state.broker = test_broker_sessionmaker

    try:
        yield
    except Exception as e:
        logging.error(f"Error when connecting to test RabbitMQ: {str(e)}")
        raise
    finally:
        await test_broker_sessionmaker.close()
        app.state.broker = old_connection


@pytest_asyncio.fixture(scope="function", autouse=True)
async def override_db_session_dependency(test_db_maker):
    engine = await test_db_maker.get_engine()

    async with engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

        async def _get_current_session():
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        app.dependency_overrides[get_session] = _get_current_session

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()

            if get_session in app.dependency_overrides:
                del app.dependency_overrides[get_session]


@pytest_asyncio.fixture(scope="function", autouse=True)
async def override_redis_session_dependency(test_cache_maker):
    session_generator = test_cache_maker.get_session()
    session = await anext(session_generator)

    async def _get_redis_session():
        return session

    app.dependency_overrides[get_redis_session] = _get_redis_session

    try:
        yield session
    finally:
        await session.flushdb()
        if get_redis_session in app.dependency_overrides:
            del app.dependency_overrides[get_redis_session]


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: AsyncClient, override_db_session_dependency):
    async def _make_headers(role: str = "user") -> dict:
        unique_id = str(ID().value)[:8]

        user_role = UserRole.USER

        match role:
            case "admin":
                user_role = UserRole.ADMIN
            case "moderator":
                user_role = UserRole.MODERATOR

        signup_payload = UserSignupRequest(
            name="testuser",
            surname="testuser",
            username=f"{role}_{unique_id}",
            password="Test1234",
            email=f"{role}_{unique_id}@email.com",
        )

        await client.post("/api/v1/auth/signup", json=signup_payload.model_dump())

        if user_role != UserRole.USER:
            db_session = override_db_session_dependency
            await db_session.execute(
                update(User)
                .where(User.username == signup_payload.username)
                .values(role=user_role)
            )
            await db_session.commit()

        login_payload = {
            "username": signup_payload.username,
            "password": signup_payload.password,
        }
        login_response = await client.post("/api/v1/auth/login", data=login_payload)
        access_token = login_response.json()["access_token"]

        return {"Authorization": f"Bearer {access_token}"}

    return _make_headers
