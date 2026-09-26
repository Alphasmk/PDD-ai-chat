import pytest
from source.application.use_cases import GetUserImage
from source.application.exceptions import (
    UserNotFoundError,
    UserHasNoImageError,
    ImageReceivingError,
)
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.storage import FakeStorage
from tests.unit.utils.shared_data import make_user, subject


async def test_only_signs_subject_key(
    repository: FakeUserRepository, storage_service: FakeStorage
) -> None:
    alice = await repository.add(make_user(image_s3_path="alice-key"))
    await repository.add(make_user("bob", "bob-key"))
    assert "alice-key" in await GetUserImage(repository, storage_service).execute(
        subject(alice)
    )
    assert storage_service.signed == ["alice-key"]


async def test_missing_user_image_and_sign_failure(
    repository: FakeUserRepository, storage_service: FakeStorage
) -> None:
    user = make_user()
    use_case = GetUserImage(repository, storage_service)
    with pytest.raises(UserNotFoundError):
        await use_case.execute(subject(user))
    await repository.add(user)
    with pytest.raises(UserHasNoImageError):
        await use_case.execute(subject(user))
    alice = await repository.add(make_user("another", "key"))
    storage_service.fail_sign = True
    with pytest.raises(ImageReceivingError):
        await use_case.execute(subject(alice))
