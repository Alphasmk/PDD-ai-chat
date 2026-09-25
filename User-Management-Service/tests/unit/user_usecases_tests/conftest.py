import pytest
from source.domain.interfaces import IPasswordHasher
from source.application.interfaces import (
    IUserRepository,
    ITokenProvider,
    ITokenBlacklist,
    IStorage,
    IMessagePublisher,
)
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.hasher import FakeHasher
from tests.adapters.token_provider import FakeTokenProvider
from tests.adapters.cache_service import FakeRedisTokenBlacklist
from tests.adapters.storage import FakeStorage
from tests.adapters.broker_service import FakeMessageService


@pytest.fixture
def repository() -> IUserRepository:
    return FakeUserRepository()


@pytest.fixture
def hasher() -> IPasswordHasher:
    return FakeHasher()


@pytest.fixture
def token_service() -> ITokenProvider:
    return FakeTokenProvider()


@pytest.fixture
def cache_service() -> ITokenBlacklist:
    return FakeRedisTokenBlacklist()


@pytest.fixture
def storage_service() -> IStorage:
    return FakeStorage()


@pytest.fixture
def message_publisher() -> IMessagePublisher:
    return FakeMessageService()
