import pytest
from source.application.use_cases import DeleteGroup
from source.application.dto import DataFromTokenDTO
from source.domain.entities.group import GroupEntity
from source.domain.value_objects import ID
from source.domain.enums.user_role import UserRole
from source.application.exceptions import (
    CannotDeleteGroupError,
    GroupNotFoundError,
)


@pytest.mark.asyncio
class TestDeleteGroup:
    async def test_success(self, repository, user_repository):
        use_case = DeleteGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        existing_group = GroupEntity(id=ID(), name="test")
        created_group = await repository.add(existing_group)

        deleted_group = await use_case.execute(created_group.id.value, current_user)

        assert deleted_group.name == "test"
        assert deleted_group.id == created_group.id.value

    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.MODERATOR],
        ids=["user_edits_group", "moderator_edits_group"],
    )
    async def test_delete_group_with_no_access(self, repository, role):
        use_case = DeleteGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=role,
        )
        existing_group = GroupEntity(id=ID(), name="test")
        created_group = await repository.add(existing_group)

        with pytest.raises(CannotDeleteGroupError):
            await use_case.execute(created_group.id.value, current_user)

    async def test_user_deletes_not_existing_group(self, repository):
        use_case = DeleteGroup(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        with pytest.raises(GroupNotFoundError):
            await use_case.execute(ID().value, current_user)
