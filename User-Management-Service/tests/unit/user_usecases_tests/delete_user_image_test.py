import pytest
from source.application.use_cases import DeleteUserImage
from source.application.exceptions import (
    UserNotFoundError,
    UserHasNoImageError,
    DeleteImageError,
)
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.storage import FakeStorage
from tests.unit.utils.shared_data import make_user, subject


async def test_only_deletes_own_key(
    repository: FakeUserRepository, storage_service: FakeStorage
) -> None:
    alice, bob = (
        await repository.add(make_user(image_s3_path="alice-key")),
        await repository.add(make_user("bob", "bob-key")),
    )
    await DeleteUserImage(repository, storage_service).execute(subject(alice))
    assert repository.users[str(alice.id.value)].image_s3_path is None
    assert repository.users[str(bob.id.value)] == bob
    assert storage_service.deleted == ["alice-key"]


async def test_missing_user_and_image(
    repository: FakeUserRepository, storage_service: FakeStorage
) -> None:
    alice = make_user()
    use_case = DeleteUserImage(repository, storage_service)
    with pytest.raises(UserNotFoundError):
        await use_case.execute(subject(alice))
    await repository.add(alice)
    with pytest.raises(UserHasNoImageError):
        await use_case.execute(subject(alice))


async def test_storage_failure_is_visible(
    repository: FakeUserRepository, storage_service: FakeStorage
) -> None:
    alice = await repository.add(make_user(image_s3_path="alice-key"))
    storage_service.fail_delete = True
    with pytest.raises(DeleteImageError):
        await DeleteUserImage(repository, storage_service).execute(subject(alice))
    assert repository.users[str(alice.id.value)].image_s3_path is None
