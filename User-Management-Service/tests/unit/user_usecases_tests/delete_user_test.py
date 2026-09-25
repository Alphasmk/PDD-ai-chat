import pytest
from tests.unit.utils.shared_data import BASE_USERS
from source.application.use_cases import DeleteUser
from source.application.dto import DataFromTokenDTO
from source.domain.entities.user import UserEntity
from source.domain.enums.user_role import UserRole
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.exceptions import UserDeleteNotAllowedError
from source.application.exceptions import ActionNotAllowedError, UserNotFoundError


@pytest.mark.asyncio
class TestDeleteUser:
    async def test_success(self, repository):
        use_case = DeleteUser(repo=repository)
        existing_user = UserEntity(
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

        user_id_to_delete = created_user.id.value

        await use_case.execute(user_id_to_delete, current_user)

        assert await repository.get_by_id(created_user.id) is None

    @pytest.mark.parametrize(
        "role, current_user_id, user_id_to_delete, user_to_delete_role, access, expected_exception",
        [
            (*BASE_USERS["A_SELF"], True, None),
            (*BASE_USERS["M_SELF"], True, None),
            (*BASE_USERS["U_SELF"], True, None),
            (*BASE_USERS["A_TO_U"], True, None),
            (*BASE_USERS["SA_TO_U"], True, None),
            (*BASE_USERS["SA_TO_A"], True, None),
            (*BASE_USERS["SA_SELF"], False, UserDeleteNotAllowedError),
            (*BASE_USERS["A_TO_SA"], False, UserDeleteNotAllowedError),
            (*BASE_USERS["M_TO_U"], False, ActionNotAllowedError),
            (*BASE_USERS["U_TO_U"], False, ActionNotAllowedError),
        ],
        ids=[
            "admin_deletes_himself",
            "moderator_deletes_himself",
            "user_deletes_himself",
            "admin_deletes_user",
            "super_admin_deletes_user",
            "super_admin_deletes_admin",
            "super_admin_deletes_himself",
            "admin_deletes_super_admin",
            "moderator_deletes_user",
            "user_deletes_user",
        ],
    )
    async def test_is_allow_to_delete_user(
        self,
        repository,
        role,
        current_user_id,
        user_id_to_delete,
        user_to_delete_role,
        access,
        expected_exception,
    ):
        use_case = DeleteUser(repo=repository)
        existing_user = UserEntity(
            id=user_id_to_delete,
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=user_to_delete_role,
        )
        created_user = await repository.add(existing_user)

        current_user = DataFromTokenDTO(
            user_id=current_user_id.value,
            email="current@current.com",
            role=role,
        )

        user_id_to_delete = created_user.id.value

        if not access:
            with pytest.raises(expected_exception):
                await use_case.execute(user_id_to_delete, current_user)
        else:
            await use_case.execute(user_id_to_delete, current_user)
            assert await repository.get_by_id(created_user.id) is None

    async def test_user_not_exists(self, repository):
        use_case = DeleteUser(repo=repository)
        user_id_to_delete = ID()

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        with pytest.raises(UserNotFoundError):
            await use_case.execute(user_id_to_delete, current_user)
