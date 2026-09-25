import pytest
from tests.unit.utils.shared_data import BASE_USERS
from source.domain.entities.user import UserEntity
from source.application.use_cases import SetUserImage
from source.application.dto import DataFromTokenDTO
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.enums.user_role import UserRole
from source.application.exceptions import (
    CannotChangeImageError,
    UserNotFoundError,
)


@pytest.mark.asyncio
class TestSetUserImage:
    @pytest.mark.parametrize(
        "role, user_id, user_id_to_change, user_role_to_change",
        (BASE_USERS["U_SELF"], BASE_USERS["A_TO_U"], BASE_USERS["SA_TO_U"]),
        ids=[
            "user_changes_himself_image",
            "admin_changes_user_image",
            "super_admin_changes_user_image",
        ],
    )
    async def test_success(
        self,
        repository,
        storage_service,
        role,
        user_id,
        user_id_to_change,
        user_role_to_change,
    ):
        use_case = SetUserImage(repo=repository, storage_service=storage_service)
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

        image = bytes("image".encode("utf-8"))
        path = await use_case.execute(image, "png", created_user.id.value, current_user)
        user_from_db = await repository.get_by_id(created_user.id)
        assert path == "avatars/uuid.png"
        assert user_from_db.image_s3_path == path

    @pytest.mark.parametrize(
        "role, user_id, user_id_to_change, user_role_to_change",
        (BASE_USERS["U_TO_U"], BASE_USERS["M_TO_U"]),
        ids=["user_changes_other_users_image", "moderator_changes_user_image"],
    )
    async def test_changing_without_access(
        self,
        repository,
        storage_service,
        role,
        user_id,
        user_id_to_change,
        user_role_to_change,
    ):
        use_case = SetUserImage(repo=repository, storage_service=storage_service)
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

        image = bytes("image".encode("utf-8"))

        with pytest.raises(CannotChangeImageError):
            await use_case.execute(image, "png", created_user.id.value, current_user)

    async def test_user_not_exists(self, repository, storage_service):
        use_case = SetUserImage(repo=repository, storage_service=storage_service)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        image = bytes("image".encode("utf-8"))

        with pytest.raises(UserNotFoundError):
            await use_case.execute(image, "png", ID().value, current_user)
