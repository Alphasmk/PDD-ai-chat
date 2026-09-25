import pytest
from source.application.use_cases import CreateGroup
from source.application.dto import DataFromTokenDTO
from source.domain.value_objects import ID
from source.domain.enums.user_role import UserRole
from source.application.exceptions import (
    CannotCreateGroupError,
    GroupAlreadyExistsError,
)


@pytest.mark.asyncio
class TestCreateGroup:
    async def test_success(self, repository):
        use_case = CreateGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        created_group = await use_case.execute("test", current_user)

        assert created_group is not None
        assert created_group.name == "test"

    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.MODERATOR],
        ids=["user_creates_group", "moderator_creates_group"],
    )
    async def test_creating_group_with_no_access(self, repository, role):
        use_case = CreateGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=role,
        )

        with pytest.raises(CannotCreateGroupError):
            await use_case.execute("test", current_user)

    async def test_group_already_exists(self, repository):
        use_case = CreateGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )

        await use_case.execute("test", current_user)

        with pytest.raises(GroupAlreadyExistsError):
            await use_case.execute("test", current_user)
