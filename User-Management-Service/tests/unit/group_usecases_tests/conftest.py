import pytest
from source.application.interfaces import IGroupRepository, IUserRepository
from tests.adapters.group_repository import FakeGroupRepository
from tests.adapters.user_repository import FakeUserRepository


@pytest.fixture
def user_repository() -> IUserRepository:
    return FakeUserRepository()


@pytest.fixture
def repository(user_repository) -> IGroupRepository:
    return FakeGroupRepository(users_data=user_repository.users)
