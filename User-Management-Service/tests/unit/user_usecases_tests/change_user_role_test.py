import pytest
from source.domain.entities.user import UserEntity
from source.application.use_cases import ChangeUserRole
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.enums.user_role import UserRole
from source.application.dto import UserRoleChangeDTO, DataFromTokenDTO
from source.domain.exceptions import (
    AdminRegularAssignError,
    RoleIsUnassignableOrChangable,
    AdminCannotChangeAdminsRoleError,
)
from source.application.exceptions import (
    ActionNotAllowedError,
    UserNotFoundError,
)


@pytest.mark.asyncio
class TestChangeUserRole:
    async def test_success(self, repository):
        use_case = ChangeUserRole(repo=repository)
        existing_user = UserEntity(
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

        role_dto = UserRoleChangeDTO(role=UserRole.MODERATOR)

        await use_case.execute(created_user.id.value, role_dto, current_user)

        changed_user = await repository.get_by_id(ID(created_user.id.value))

        assert changed_user.role == UserRole.MODERATOR

    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.MODERATOR],
        ids=["changes_with_user_role", "changes_with_moderator_role"],
    )
    async def test_user_have_no_access_to_change_role(self, repository, role):
        use_case = ChangeUserRole(repo=repository)
        existing_user = UserEntity(
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
            role=role,
        )

        role_dto = UserRoleChangeDTO(role=UserRole.MODERATOR)

        with pytest.raises(ActionNotAllowedError):
            await use_case.execute(created_user.id.value, role_dto, current_user)

    async def test_user_not_found(self, repository):
        use_case = ChangeUserRole(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        role_dto = UserRoleChangeDTO(role=UserRole.MODERATOR)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(ID().value, role_dto, current_user)

    async def test_admin_changes_admins_role(self, repository):
        use_case = ChangeUserRole(repo=repository)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=UserRole.ADMIN,
        )
        created_user = await repository.add(existing_user)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        role_dto = UserRoleChangeDTO(role=UserRole.MODERATOR)

        with pytest.raises(AdminCannotChangeAdminsRoleError):
            await use_case.execute(created_user.id.value, role_dto, current_user)

    async def test_admin_assigns_another_admin(self, repository):
        use_case = ChangeUserRole(repo=repository)
        existing_user = UserEntity(
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

        role_dto = UserRoleChangeDTO(role=UserRole.ADMIN)

        with pytest.raises(AdminRegularAssignError):
            await use_case.execute(created_user.id.value, role_dto, current_user)

    async def test_user_role_is_not_assignable(self, repository):
        use_case = ChangeUserRole(repo=repository)
        existing_user = UserEntity(
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

        role_dto = UserRoleChangeDTO(role=UserRole.SUPER_ADMIN)

        with pytest.raises(RoleIsUnassignableOrChangable):
            await use_case.execute(created_user.id.value, role_dto, current_user)

    async def test_user_role_is_not_changable(self, repository):
        use_case = ChangeUserRole(repo=repository)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
            role=UserRole.SUPER_ADMIN,
        )
        created_user = await repository.add(existing_user)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        role_dto = UserRoleChangeDTO(role=UserRole.MODERATOR)

        with pytest.raises(RoleIsUnassignableOrChangable):
            await use_case.execute(created_user.id.value, role_dto, current_user)
