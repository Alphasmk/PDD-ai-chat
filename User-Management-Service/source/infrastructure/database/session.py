from collections.abc import AsyncIterator
import logging
from functools import lru_cache
from types import TracebackType
from typing import Self
from sqlalchemy.exc import SQLAlchemyError
from source.application.interfaces.unit_of_work import IUserUnitOfWork
from source.application.exceptions.user_exceptions import ServiceUnavailableError
from source.infrastructure.database.user_repository import UserRepository
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from source.infrastructure.interfaces import IDatabaseSessionmaker


class DatabaseSessionmaker(IDatabaseSessionmaker):
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    async def init_db(self, db_url: str) -> None:
        self._engine = create_async_engine(str(db_url), echo=False, future=True)
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logging.info("Created connection with database")

    async def get_session(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker:
            async with self._session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    logging.warning("Database transaction rolled back")
                    raise
                finally:
                    await session.close()
        else:
            logging.warning("Sessionmaker not initialized")

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None
            logging.info("Database connection closed")

    async def get_engine(self) -> AsyncEngine | None:
        return self._engine


@lru_cache
def get_database() -> IDatabaseSessionmaker:
    return DatabaseSessionmaker()


class UserUnitOfWork(IUserUnitOfWork):
    def __init__(self, maker: async_sessionmaker[AsyncSession]) -> None:
        self.maker = maker

    async def __aenter__(self) -> Self:
        self.session = self.maker()
        self.repository = UserRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            await self.rollback()
        finally:
            await self.session.close()
        if isinstance(exc, (SQLAlchemyError, OSError)):
            raise ServiceUnavailableError() from exc

    async def commit(self) -> None:
        try:
            await self.session.commit()
        except (SQLAlchemyError, OSError) as error:
            raise ServiceUnavailableError() from error

    async def rollback(self) -> None:
        try:
            await self.session.rollback()
        except (SQLAlchemyError, OSError) as error:
            raise ServiceUnavailableError() from error
