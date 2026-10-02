import asyncio
from collections.abc import Callable
from time import monotonic
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from source.application.use_cases.bootstrap_use_case import (
    BootstrapSuperadmin,
    BootstrapData,
    InitializationError,
)
from source.infrastructure.database.user_repository import UserRepository
from source.infrastructure.hasher.password_hasher import PasswordHasher

INITIALIZATION_LOCK = 74004001


def migrate(connection: Connection) -> None:
    config = Config("alembic.ini")
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


async def initialize_service(
    database_url: str,
    initial: Callable[[], BootstrapData],
    schema: str | None = None,
    lock_timeout: float = 60.0,
) -> bool:
    if not database_url.startswith("postgresql+asyncpg://"):
        raise InitializationError("database_unavailable")
    options: dict[str, object] = {"timeout": 10}
    if schema is not None:
        if not schema.startswith("ums_test_") or not schema.replace("_", "").isalnum():
            raise InitializationError("invalid_initial_data")
        options["server_settings"] = {"search_path": schema}
    engine = create_async_engine(database_url, poolclass=NullPool, connect_args=options)
    try:
        async with engine.connect() as connection:
            acquired = False
            try:
                deadline = monotonic() + lock_timeout
                while True:
                    acquired = bool(
                        await connection.scalar(
                            text("SELECT pg_try_advisory_lock(:key)"),
                            {"key": INITIALIZATION_LOCK},
                        )
                    )
                    await connection.commit()
                    if acquired:
                        break
                    if monotonic() >= deadline:
                        raise InitializationError("initialization_timeout")
                    await asyncio.sleep(0.1)
                await connection.run_sync(migrate)
                await connection.commit()
                async with AsyncSession(
                    bind=connection, expire_on_commit=False
                ) as session:
                    created = await BootstrapSuperadmin(
                        UserRepository(session), PasswordHasher()
                    ).execute(initial)
                    await session.commit()
                return created
            finally:
                await connection.rollback()
                if acquired:
                    await connection.execute(
                        text("SELECT pg_advisory_unlock(:key)"),
                        {"key": INITIALIZATION_LOCK},
                    )
                    await connection.commit()
    finally:
        await engine.dispose()
