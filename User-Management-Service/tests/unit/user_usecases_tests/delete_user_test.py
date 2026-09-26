import pytest
from source.application.use_cases import DeleteUser
from source.application.exceptions import UserNotFoundError
from tests.adapters.user_repository import FakeUserRepository
from tests.unit.utils.shared_data import make_user, subject


async def test_deletes_subject_only(repository: FakeUserRepository) -> None:
    alice, bob = (
        await repository.add(make_user()),
        await repository.add(make_user("bob")),
    )
    result = await DeleteUser(repository).execute(subject(alice))
    assert result.id == alice.id.value
    assert repository.users == {str(bob.id.value): bob}
    with pytest.raises(UserNotFoundError):
        await DeleteUser(repository).execute(subject(alice))
