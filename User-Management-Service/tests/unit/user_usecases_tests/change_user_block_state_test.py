import pytest
from tests.unit.utils.shared_data import BASE_USERS
from source.application.use_cases.user_use_cases import ChangeUserBlockState
from source.application.dto import DataFromTokenDTO
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.entities.user import UserEntity
from source.domain.enums.user_role import UserRole
from source.domain.exceptions import CannotBlockAdminError
from source.application.exceptions import (
    UserNotFoundError,
    ActionNotAllowedError,
)


@pytest.mark.asyncio
class TestChangeUserBlockState:
    async def test_success(self, repository):
        use_case = ChangeUserBlockState(repo=repository)
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
            user_id=ID().value, email="current@current.com", role=UserRole.ADMIN
        )

        await use_case.execute(created_user.id.value, current_user)
        user_from_db = await repository.get_by_id(created_user.id)
        assert user_from_db.is_blocked

        await use_case.execute(created_user.id.value, current_user)
        user_from_db = await repository.get_by_id(created_user.id)
        assert not user_from_db.is_blocked

    async def test_user_not_exists(self, repository):
        use_case = ChangeUserBlockState(repo=repository)
        user_id = ID()
        current_user = DataFromTokenDTO(
            user_id=ID().value, email="current@current.com", role=UserRole.ADMIN
        )
        with pytest.raises(UserNotFoundError):
            await use_case.execute(user_id.value, current_user)

    @pytest.mark.parametrize(
        "role, current_user_id, block_user_id, block_user_role, expected_exception",
        [
            (*BASE_USERS["M_TO_U"], ActionNotAllowedError),
            (*BASE_USERS["U_TO_U"], ActionNotAllowedError),
            (*BASE_USERS["A_TO_SA"], CannotBlockAdminError),
            (*BASE_USERS["SA_TO_A"], CannotBlockAdminError),
        ],
        ids=[
            "moderator_blocks_user",
            "user_blocks_user",
            "admin_blocks_super_admin",
            "super_admin_blocks_admin",
        ],
    )
    async def test_block_user_with_no_access(
        self,
        repository,
        role,
        current_user_id,
        block_user_id,
        block_user_role,
        expected_exception,
    ):
        use_case = ChangeUserBlockState(repo=repository)
        existing_user = UserEntity(
            id=block_user_id,
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=block_user_role,
        )

        created_user = await repository.add(existing_user)

        current_user = DataFromTokenDTO(
            user_id=current_user_id, email="current@current.com", role=role
        )

        with pytest.raises(expected_exception):
            await use_case.execute(created_user.id.value, current_user)
