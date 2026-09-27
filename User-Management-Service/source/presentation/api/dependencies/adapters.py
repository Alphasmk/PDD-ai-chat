from collections.abc import AsyncIterator
from redis.asyncio import Redis
from source.infrastructure.interfaces import (
    IBrokerHandler,
    IDatabaseSessionmaker,
    ICacheSessionmaker,
)
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from source.application.interfaces.unit_of_work import UnitOfWorkFactory
from source.infrastructure.database.session import UserUnitOfWork
from source.application.interfaces.roles import IRoleRepository
from source.infrastructure.database.role_repository import RoleRepository
from source.application.interfaces import (
    IUserRepository,
    ITokenProvider,
    ITokenBlacklist,
    IMessagePublisher,
)
from source.domain.interfaces import IPasswordHasher
from source.infrastructure.database import get_database
from source.infrastructure.cache import get_cache_database, RedisTokenBlacklist
from source.infrastructure.database import UserRepository
from source.infrastructure.hasher.password_hasher import PasswordHasher
from source.infrastructure.jwt import TokenProvider
from source.infrastructure.message_broker import MessagePublisher
from source.settings.config import get_settings, Config


async def get_session(
    database: IDatabaseSessionmaker = Depends(get_database),
) -> AsyncIterator[AsyncSession]:
    async for session in database.get_session():
        yield session


async def get_redis_session(
    database: ICacheSessionmaker = Depends(get_cache_database),
) -> AsyncIterator[Redis]:
    async for session in database.get_session():
        yield session


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> IUserRepository:
    return UserRepository(session=session)


async def get_role_repository(
    session: AsyncSession = Depends(get_session),
) -> IRoleRepository:
    return RoleRepository(session)


async def get_unit_of_work_factory(
    session: AsyncSession = Depends(get_session),
) -> UnitOfWorkFactory:
    maker = async_sessionmaker(session.bind, expire_on_commit=False)
    return lambda: UserUnitOfWork(maker)


async def get_password_hasher() -> IPasswordHasher:
    return PasswordHasher()


async def get_message_broker_handler(req: Request) -> IBrokerHandler:
    handler: object = req.app.state.broker
    if not isinstance(handler, IBrokerHandler):
        raise RuntimeError("Broker not initialized")
    return handler


async def get_message_broker_service(
    handler: IBrokerHandler = Depends(get_message_broker_handler),
) -> IMessagePublisher:
    return MessagePublisher(handler=handler)


async def get_token_service(settings: Config = Depends(get_settings)) -> ITokenProvider:
    return TokenProvider(
        secret_key=settings.auth.secret_key.get_secret_value(),
        algorithm=settings.auth.algorithm,
        access_expire_minutes=settings.auth.access_token_expire_minutes,
        refresh_expire_days=settings.auth.refresh_token_expire_days,
    )


async def get_cache_service(
    session: Redis = Depends(get_redis_session),
) -> ITokenBlacklist:
    return RedisTokenBlacklist(redis_client=session)
