import pytest
from source.application.use_cases import GetUserImage
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.entities.user import UserEntity
from source.application.exceptions import (
    UserNotFoundError,
    UserHasNoImageError,
)


@pytest.mark.asyncio
class TestGetUserImage:
    async def test_success(self, repository, storage_service):
        use_case = GetUserImage(repo=repository, storage_service=storage_service)
        existing_user = UserEntity(
            id=ID(),
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            image_s3_path="avatars/uuid.png",
        )

        created_user = await repository.add(existing_user)

        path = await use_case.execute(created_user.id.value)

        assert path == "https://s3.com/avatars/uuid.png"

    async def test_user_not_exists(self, repository, storage_service):
        use_case = GetUserImage(repo=repository, storage_service=storage_service)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(ID().value)

    async def test_user_has_no_image(self, repository, storage_service):
        use_case = GetUserImage(repo=repository, storage_service=storage_service)
        existing_user = UserEntity(
            id=ID(),
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )

        created_user = await repository.add(existing_user)

        with pytest.raises(UserHasNoImageError):
            await use_case.execute(created_user.id.value)
