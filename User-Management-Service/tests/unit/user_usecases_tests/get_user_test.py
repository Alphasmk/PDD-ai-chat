import pytest
from uuid import UUID
from tests.unit.utils.shared_data import BASE_USERS
from source.application.use_cases import GetUser
from source.application.dto import DataFromTokenDTO
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.entities.user import UserEntity
from source.domain.enums.user_role import UserRole
from source.application.exceptions import (
    UserNotFoundError,
    ModeratorGetInfoNotAllowed,
    UserGetInfoNotAllowed,
)


@pytest.mark.asyncio
class TestGetUser:
    async def test_success(self, repository):
        use_case = GetUser(repo=repository)
        existing_user = UserEntity(
            id=ID(),
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=UserRole.USER,
        )

        created_user = await repository.add(existing_user)

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        user_from_db = await use_case.execute(created_user.id.value, current_user)

        assert user_from_db.id == created_user.id.value
        assert user_from_db.name == created_user.name.value
        assert user_from_db.surname == created_user.surname.value
        assert user_from_db.username == created_user.username
        assert user_from_db.email == created_user.email.value

    async def test_user_not_exists(self, repository):
        use_case = GetUser(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        with pytest.raises(UserNotFoundError):
            await use_case.execute(ID(), current_user)

    @pytest.mark.parametrize(
        "role, current_user_id, get_user_id, get_user_role, current_user_group_id, get_user_group_id, access, expected_exception",
        [
            (*BASE_USERS["M_TO_U"], ID(), ID(), False, ModeratorGetInfoNotAllowed),
            (
                *BASE_USERS["M_TO_U"],
                ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
                ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
                True,
                None,
            ),
        ],
        ids=[
            "moderator_edits_user_not_from_its_own_group",
            "moderator_edits_user_from_its_own_group",
        ],
    )
    async def test_moderator_get_info_about_user(
        self,
        repository,
        role,
        current_user_id,
        get_user_id,
        get_user_role,
        current_user_group_id,
        get_user_group_id,
        access,
        expected_exception,
    ):
        use_case = GetUser(repo=repository)
        existing_user = UserEntity(
            id=get_user_id,
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=get_user_role,
            group_id=get_user_group_id.value,
        )

        created_user = await repository.add(existing_user)

        current_user = DataFromTokenDTO(
            user_id=current_user_id.value,
            email="current@current.com",
            role=role,
            group_id=current_user_group_id.value,
        )

        if not access:
            with pytest.raises(expected_exception):
                await use_case.execute(created_user.id.value, current_user)
        else:
            user_from_db = await use_case.execute(created_user.id.value, current_user)
            assert user_from_db.id == created_user.id.value
            assert user_from_db.name == created_user.name.value
            assert user_from_db.surname == created_user.surname.value
            assert user_from_db.username == created_user.username
            assert user_from_db.email == created_user.email.value

    @pytest.mark.parametrize(
        "role, current_user_id, get_user_id, get_user_role",
        [
            BASE_USERS["U_TO_U"],
            BASE_USERS["U_TO_M"],
            BASE_USERS["U_TO_A"],
        ],
        ids=["user_edits_user", "user_edits_moderator", "user_edits_admin"],
    )
    async def test_user_try_to_edit_someone(
        self, repository, role, current_user_id, get_user_id, get_user_role
    ):
        use_case = GetUser(repo=repository)
        existing_user = UserEntity(
            id=get_user_id,
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=get_user_role,
        )

        created_user = await repository.add(existing_user)

        current_user = DataFromTokenDTO(
            user_id=current_user_id.value,
            email="current@current.com",
            role=role,
        )

        with pytest.raises(UserGetInfoNotAllowed):
            await use_case.execute(created_user.id.value, current_user)
