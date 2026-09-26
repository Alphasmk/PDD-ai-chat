import pytest
from source.application.use_cases import SetUserImage
from source.application.exceptions import (
    UserNotFoundError,
    UploadImageError,
    DeleteImageError,
)
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.storage import FakeStorage
from tests.unit.utils.shared_data import make_user, subject


async def test_replace_own_image(
    repository: FakeUserRepository, storage_service: FakeStorage
) -> None:
    alice, bob = (
        await repository.add(make_user(image_s3_path="old")),
        await repository.add(make_user("bob", "bob-key")),
    )
    path = await SetUserImage(repository, storage_service).execute(
        b"image", ".png", subject(alice)
    )
    assert repository.users[str(alice.id.value)].image_s3_path == path
    assert storage_service.deleted == ["old"]
    assert repository.users[str(bob.id.value)] == bob


async def test_missing_user_and_upload_failure(
    repository: FakeUserRepository, storage_service: FakeStorage
) -> None:
    user = make_user(image_s3_path="old")
    use_case = SetUserImage(repository, storage_service)
    with pytest.raises(UserNotFoundError):
        await use_case.execute(b"image", ".png", subject(user))
    await repository.add(user)
    storage_service.fail_upload = True
    with pytest.raises(UploadImageError):
        await use_case.execute(b"image", ".png", subject(user))
    assert repository.users[str(user.id.value)] == user and not storage_service.deleted


async def test_replacement_delete_failure_preserves_new_reference(
    repository: FakeUserRepository, storage_service: FakeStorage
) -> None:
    user = await repository.add(make_user(image_s3_path="old"))
    storage_service.fail_delete = True
    with pytest.raises(DeleteImageError):
        await SetUserImage(repository, storage_service).execute(
            b"image", ".png", subject(user)
        )
    assert repository.users[str(user.id.value)].image_s3_path != "old"
