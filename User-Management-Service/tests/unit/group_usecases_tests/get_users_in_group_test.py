import pytest
from source.application.use_cases import GetUsersInGroup
from source.application.dto import DataFromTokenDTO
from source.domain.entities.group import GroupEntity
from source.domain.entities.user import UserEntity
from source.domain.enums.user_role import UserRole
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.application.exceptions import (
    CannotGetGroupUsersError,
    GroupNotFoundError,
)


@pytest.mark.asyncio
class TestGetUsersInGroup:
    @pytest.mark.parametrize(
        "role",
        [UserRole.ADMIN, UserRole.SUPER_ADMIN],
        ids=["admin_gets_users", "super_admin_gets_users"],
    )
    async def test_success_admin_roles(self, user_repository, repository, role):
        use_case = GetUsersInGroup(repo=repository)

        existing_group = GroupEntity(id=ID(), name="test_group")
        created_group = await repository.add(existing_group)

        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        created_user = await user_repository.add(existing_user)
        await repository.add_user_to_group(created_group.id, created_user.id)

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=role,
        )

        users = await use_case.execute(created_group.id.value, current_user)

        assert len(users) == 1
        assert users[0].id == created_user.id.value
        assert users[0].username == created_user.username

    async def test_moderator_gets_users_from_his_group(self, repository):
        use_case = GetUsersInGroup(repo=repository)

        existing_group = GroupEntity(id=ID(), name="moderator_group")
        created_group = await repository.add(existing_group)

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.MODERATOR,
            group_id=created_group.id.value,
        )

        users = await use_case.execute(created_group.id.value, current_user)

        assert isinstance(users, list)

    async def test_moderator_gets_users_from_other_group(self, repository):
        use_case = GetUsersInGroup(repo=repository)
        target_group = GroupEntity(id=ID(), name="target_group")
        created_group = await repository.add(target_group)

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.MODERATOR,
            group_id=ID().value,
        )

        with pytest.raises(CannotGetGroupUsersError):
            await use_case.execute(created_group.id.value, current_user)

    async def test_user_have_no_access(self, repository):
        use_case = GetUsersInGroup(repo=repository)

        existing_group = GroupEntity(id=ID(), name="test")
        created_group = await repository.add(existing_group)

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.USER,
            group_id=created_group.id.value,
        )

        with pytest.raises(CannotGetGroupUsersError):
            await use_case.execute(created_group.id.value, current_user)

    async def test_group_not_exists(self, repository):
        use_case = GetUsersInGroup(repo=repository)

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        with pytest.raises(GroupNotFoundError):
            await use_case.execute(ID().value, current_user)
