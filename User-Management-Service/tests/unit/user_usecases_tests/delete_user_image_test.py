import pytest
from tests.unit.utils.shared_data import BASE_USERS
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.enums.user_role import UserRole
from source.domain.entities.user import UserEntity
from source.application.use_cases import DeleteUserImage
from source.application.dto import DataFromTokenDTO
from source.application.exceptions import (
    UserNotFoundError,
    CannotDeleteImageError,
    UserHasNoImageError,
)


@pytest.mark.asyncio
class TestDeleteUserImage:
    async def test_success(self, repository, storage_service):
        use_case = DeleteUserImage(repo=repository, storage_service=storage_service)
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

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        await use_case.execute(created_user.id.value, current_user)

        user_from_db = await repository.get_by_id(created_user.id)

        assert user_from_db.image_s3_path is None

    async def test_user_not_exists(self, repository, storage_service):
        use_case = DeleteUserImage(repo=repository, storage_service=storage_service)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        with pytest.raises(UserNotFoundError):
            await use_case.execute(ID().value, current_user)

    @pytest.mark.parametrize(
        "role, user_id, user_id_to_change, user_role_to_change",
        (BASE_USERS["U_TO_U"], BASE_USERS["M_TO_U"]),
        ids=["user_deletes_other_users_image", "moderator_deletes_user_image"],
    )
    async def test_delete_without_access(
        self,
        repository,
        storage_service,
        role,
        user_id,
        user_id_to_change,
        user_role_to_change,
    ):
        use_case = DeleteUserImage(repo=repository, storage_service=storage_service)
        existing_user = UserEntity(
            id=user_id_to_change,
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=user_role_to_change,
        )

        created_user = await repository.add(existing_user)

        current_user = DataFromTokenDTO(
            user_id=user_id.value,
            email="current@current.com",
            role=role,
        )

        with pytest.raises(CannotDeleteImageError):
            await use_case.execute(created_user.id.value, current_user)

    async def test_user_has_no_image(self, repository, storage_service):
        use_case = DeleteUserImage(repo=repository, storage_service=storage_service)
        existing_user = UserEntity(
            id=ID(),
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )

        created_user = await repository.add(existing_user)

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        with pytest.raises(UserHasNoImageError):
            await use_case.execute(created_user.id.value, current_user)
