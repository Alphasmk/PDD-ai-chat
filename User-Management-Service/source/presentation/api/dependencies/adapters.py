from fastapi import Depends, Request
from aioboto3 import Session
from sqlalchemy.ext.asyncio import AsyncSession
from source.application.interfaces import (
    IUserRepository,
    ITokenProvider,
    ITokenBlacklist,
    IMessagePublisher,
    IBrokerHandler,
    IGroupRepository,
    IDatabaseSessionmaker,
    ICacheSessionmaker,
    IStorage,
)
from source.infrastructure.storage.session import get_aws_session
from source.domain.interfaces import IPasswordHasher
from source.infrastructure.database import get_database
from source.infrastructure.cache import get_cache_database, RedisTokenBlacklist
from source.infrastructure.database import UserRepository, GroupRepository
from source.infrastructure.hasher.password_hasher import PasswordHasher
from source.infrastructure.jwt import TokenProvider
from source.infrastructure.message_broker import MessagePublisher
from source.infrastructure.storage.storage_adapter import Storage
from source.application.use_cases import CreateSuperUser
from source.settings.config import get_settings, Config


async def get_session(database: IDatabaseSessionmaker = Depends(get_database)):
    async for session in database.get_session():
        yield session


async def get_redis_session(database: ICacheSessionmaker = Depends(get_cache_database)):
    async for session in database.get_session():
        yield session


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> IUserRepository:
    return UserRepository(session=session)


async def get_group_repository(
    session: AsyncSession = Depends(get_session),
) -> IGroupRepository:
    return GroupRepository(session=session)


async def get_password_hasher() -> IPasswordHasher:
    return PasswordHasher()


async def get_message_broker_handler(req: Request) -> IBrokerHandler:
    return req.app.state.broker


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


async def get_cache_service(session=Depends(get_redis_session)) -> ITokenBlacklist:
    return RedisTokenBlacklist(redis_client=session)


async def get_storage(
    session: Session = Depends(get_aws_session),
    settings: Config = Depends(get_settings),
) -> IStorage:
    return Storage(session=session, bucket_name=settings.storage.bucket_name)


def create_super_user_factory(session: AsyncSession) -> CreateSuperUser:
    repo = UserRepository(session)
    hasher = PasswordHasher()
    return CreateSuperUser(repo, hasher)
