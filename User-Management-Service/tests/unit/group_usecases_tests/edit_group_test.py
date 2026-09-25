import pytest
from source.application.use_cases import EditGroup
from source.application.dto import DataFromTokenDTO, GroupEditDTO
from source.domain.entities.group import GroupEntity
from source.domain.value_objects import ID
from source.domain.enums.user_role import UserRole
from source.application.exceptions import (
    CannotEditGroupError,
    GroupAlreadyExistsError,
    GroupNotFoundError,
)


@pytest.mark.asyncio
class TestEditGroup:
    async def test_success(self, repository):
        use_case = EditGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        existing_group = GroupEntity(id=ID(), name="test")
        created_group = await repository.add(existing_group)

        data = GroupEditDTO(name="new_name")

        edited_group = await use_case.execute(
            created_group.id.value, data, current_user
        )

        assert edited_group.name == "new_name"

    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.MODERATOR],
        ids=["user_edits_group", "moderator_edits_group"],
    )
    async def test_edit_group_with_no_access(self, repository, role):
        use_case = EditGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=role,
        )
        existing_group = GroupEntity(id=ID(), name="test")
        created_group = await repository.add(existing_group)

        data = GroupEditDTO(name="new_name")

        with pytest.raises(CannotEditGroupError):
            await use_case.execute(created_group.id.value, data, current_user)

    async def test_edit_group_with_duplicate_name(self, repository):
        use_case = EditGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        existing_group = GroupEntity(id=ID(), name="test1")
        await repository.add(existing_group)
        existing_group = GroupEntity(id=ID(), name="test2")
        created_group = await repository.add(existing_group)
        data = GroupEditDTO(name="test1")

        with pytest.raises(GroupAlreadyExistsError):
            await use_case.execute(created_group.id.value, data, current_user)

    async def test_user_edits_not_existing_group(self, repository):
        use_case = EditGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        data = GroupEditDTO(name="test")
        with pytest.raises(GroupNotFoundError):
            await use_case.execute(ID().value, data, current_user)
