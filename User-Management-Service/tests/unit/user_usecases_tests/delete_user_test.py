import pytest
from source.application.use_cases import DeleteUser
from source.application.exceptions import UserNotFoundError
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.unit_of_work import FakeUnitOfWork
from dataclasses import replace
from source.domain.value_objects.user_role import UserRole
from source.application.exceptions.user_exceptions import (
    ProtectedAccountError,
    ServiceUnavailableError,
)
from tests.unit.utils.shared_data import make_user, subject


async def test_deletes_subject_only(repository: FakeUserRepository) -> None:
    alice, bob = (
        await repository.add(make_user()),
        await repository.add(make_user("bob")),
    )
    result = await DeleteUser(lambda: FakeUnitOfWork(repository)).execute(
        subject(alice)
    )
    assert result.id == alice.id.value
    assert repository.users == {str(bob.id.value): bob}
    with pytest.raises(UserNotFoundError):
        await DeleteUser(lambda: FakeUnitOfWork(repository)).execute(subject(alice))


async def test_protected_delete_and_commit_failure(
    repository: FakeUserRepository,
) -> None:
    owner = await repository.add(
        replace(make_user("owner"), role=UserRole.ADMIN, is_superadmin=True)
    )
    with pytest.raises(ProtectedAccountError):
        await DeleteUser(lambda: FakeUnitOfWork(repository)).execute(subject(owner))
    user = await repository.add(make_user())
    with pytest.raises(ServiceUnavailableError):
        await DeleteUser(lambda: FakeUnitOfWork(repository, fail_commit=True)).execute(
            subject(user)
        )
    assert await repository.get_by_id(user.id) == user
