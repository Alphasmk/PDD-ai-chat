import pytest
from datetime import datetime
from source.application.use_cases import AddUserToGroup
from source.application.dto import UserReadDTO
from source.domain.entities.group import GroupEntity
from source.domain.entities.user import UserEntity
from source.domain.enums.user_role import UserRole
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.application.exceptions import (
    CannotAddUserToGroupError,
    GroupNotFoundError,
    UserNotFoundError,
)


@pytest.mark.asyncio
class TestAddUserToGroup:
    async def test_success(self, user_repository, repository):
        use_case = AddUserToGroup(repo=repository)
        existing_group = GroupEntity(id=ID(), name="test")
        created_group = await repository.add(existing_group)

        current_user = UserReadDTO(
            id=ID(),
            name="current",
            surname="current",
            username="current",
            email="current@current.com",
            role=UserRole.ADMIN,
            created_at=datetime.now(),
        )

        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        created_user = await user_repository.add(existing_user)

        await use_case.execute(
            created_group.id.value, created_user.id.value, current_user
        )

        updated_user = await user_repository.get_by_id(created_user.id)
        assert updated_user.group_id == created_group.id.value
        is_in_group = await repository.is_user_in_group(
            created_group.id, created_user.id
        )
        assert is_in_group is True

    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.MODERATOR],
        ids=["user_adds_another_user", "moderator_adds_user"],
    )
    async def test_adds_user_to_group_with_no_access(
        self, user_repository, repository, role
    ):
        use_case = AddUserToGroup(repo=repository)
        existing_group = GroupEntity(id=ID(), name="test")
        created_group = await repository.add(existing_group)

        current_user = UserReadDTO(
            id=ID(),
            name="current",
            surname="current",
            username="current",
            email="current@current.com",
            role=role,
            created_at=datetime.now(),
        )

        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        created_user = await user_repository.add(existing_user)

        with pytest.raises(CannotAddUserToGroupError):
            await use_case.execute(
                created_group.id.value, created_user.id.value, current_user
            )

    async def test_adds_to_not_existing_group(self, user_repository, repository):
        use_case = AddUserToGroup(repo=repository)

        current_user = UserReadDTO(
            id=ID(),
            name="current",
            surname="current",
            username="current",
            email="current@current.com",
            role=UserRole.ADMIN,
            created_at=datetime.now(),
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )

        created_user = await user_repository.add(existing_user)

        with pytest.raises(GroupNotFoundError):
            await use_case.execute(ID().value, created_user.id.value, current_user)

    async def test_adds_not_existing_user(self, repository):
        use_case = AddUserToGroup(repo=repository)
        existing_group = GroupEntity(id=ID(), name="test")
        created_group = await repository.add(existing_group)

        current_user = UserReadDTO(
            id=ID(),
            name="current",
            surname="current",
            username="current",
            email="current@current.com",
            role=UserRole.ADMIN,
            created_at=datetime.now(),
        )

        with pytest.raises(UserNotFoundError):
            await use_case.execute(created_group.id.value, ID().value, current_user)
