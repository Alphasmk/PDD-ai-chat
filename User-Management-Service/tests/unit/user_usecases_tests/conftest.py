import pytest
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.hasher import FakeHasher
from tests.adapters.token_provider import FakeTokenProvider
from tests.adapters.cache_service import FakeRedisTokenBlacklist
from tests.adapters.storage import FakeStorage
from tests.adapters.broker_service import FakeMessageService


@pytest.fixture
def repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def hasher() -> FakeHasher:
    return FakeHasher()


@pytest.fixture
def token_service() -> FakeTokenProvider:
    return FakeTokenProvider()


@pytest.fixture
def cache_service() -> FakeRedisTokenBlacklist:
    return FakeRedisTokenBlacklist()


@pytest.fixture
def storage_service() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def message_publisher() -> FakeMessageService:
    return FakeMessageService()
