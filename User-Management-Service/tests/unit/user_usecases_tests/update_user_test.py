import pytest
from tests.unit.utils.shared_data import BASE_USERS
from source.application.use_cases import UpdateUser
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.enums.user_role import UserRole
from source.application.dto import UpdateUserDTO, DataFromTokenDTO, UserReadDTO
from source.domain.entities.user import UserEntity
from source.application.exceptions import (
    UserNotFoundError,
    ActionNotAllowedError,
    UserEditNotAllowedError,
)


@pytest.mark.asyncio
class TestUpdateUser:
    async def test_success(self, repository):
        use_case = UpdateUser(repo=repository)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        await repository.add(existing_user)

        update_data = UpdateUserDTO(name="newname", surname="newsurname")

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        updated_user = await use_case.execute(
            existing_user.id.value, current_user, update_data
        )

        assert updated_user is not None
        assert updated_user.name == "newname"
        assert updated_user.surname == "newsurname"

    async def test_user_to_edit_not_found(self, repository):
        use_case = UpdateUser(repo=repository)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        await repository.add(existing_user)

        update_data = UpdateUserDTO(name="newname", surname="newsurname")

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        fake_id = ID()

        with pytest.raises(UserNotFoundError):
            await use_case.execute(fake_id.value, current_user, update_data)

    @pytest.mark.parametrize(
        "role, current_user_id, edit_user_id, user_to_edit_role, access, expected_exception",
        [
            (*BASE_USERS["SA_SELF"], True, None),
            (*BASE_USERS["A_SELF"], True, None),
            (*BASE_USERS["M_SELF"], True, None),
            (*BASE_USERS["U_SELF"], True, None),
            (*BASE_USERS["A_TO_U"], True, None),
            (*BASE_USERS["SA_TO_U"], True, None),
            (*BASE_USERS["SA_TO_A"], True, None),
            (*BASE_USERS["A_TO_SA"], False, UserEditNotAllowedError),
            (*BASE_USERS["M_TO_U"], False, ActionNotAllowedError),
            (*BASE_USERS["U_TO_U"], False, ActionNotAllowedError),
        ],
        ids=[
            "super_admin_edits_himself",
            "admin_edits_himself",
            "moderator_edits_himself",
            "user_edits_himself",
            "admin_edits_user",
            "super_admin_edits_user",
            "super_admin_edits_admin",
            "admin_edits_super_admin",
            "moderator_edits_user",
            "user_edits_user",
        ],
    )
    async def test_is_allow_to_edit_user(
        self,
        repository,
        role,
        current_user_id,
        edit_user_id,
        user_to_edit_role,
        access,
        expected_exception,
    ):
        use_case = UpdateUser(repo=repository)
        existing_user = UserEntity(
            id=edit_user_id,
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=user_to_edit_role,
        )
        await repository.add(existing_user)

        update_data = UpdateUserDTO(
            name="newname", surname="newsurname", email="newemail@newemail.com"
        )

        current_user = DataFromTokenDTO(
            user_id=current_user_id.value,
            email="current@current.com",
            role=role,
        )
        if not access:
            with pytest.raises(expected_exception):
                await use_case.execute(
                    existing_user.id.value, current_user, update_data
                )
        else:
            edited_user = await use_case.execute(
                existing_user.id.value, current_user, update_data
            )
            assert edited_user is not None

    async def test_update_data_is_none(self, repository):
        use_case = UpdateUser(repo=repository)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        await repository.add(existing_user)

        update_data = UpdateUserDTO()

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        expected_user = UserReadDTO(
            id=existing_user.id.value,
            name=existing_user.name.value,
            surname=existing_user.surname.value,
            username=existing_user.username,
            email=existing_user.email.value,
            role=existing_user.role,
            created_at=existing_user.created_at,
            phone_number=existing_user.phone_number,
        )

        updated_user = await use_case.execute(
            existing_user.id.value, current_user, update_data
        )

        assert expected_user == updated_user
