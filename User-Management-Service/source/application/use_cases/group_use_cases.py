from typing import List
from uuid import UUID

from source.application.dto import (
    GroupReadDTO,
    GroupEditDTO,
    UserReadDTO,
    DataFromTokenDTO,
)
from source.application.use_cases.base import UseCaseBase
from source.domain.enums.user_role import UserRole
from source.domain.entities.group import GroupEntity as Group
from source.domain.value_objects import ID
from source.application.interfaces import IGroupRepository
from source.application.exceptions import (
    UserNotFoundError,
    CannotCreateGroupError,
    CannotEditGroupError,
    CannotDeleteGroupError,
    CannotAddUserToGroupError,
    CannotGetGroupUsersError,
    CannotRemoveUserFromGroupError,
    GroupNotFoundError,
    GroupAlreadyExistsError,
)


class CreateGroup(UseCaseBase):
    def __init__(self, repo: IGroupRepository):
        self.repo = repo

    async def execute(
        self, name: str, current_user: DataFromTokenDTO
    ) -> GroupReadDTO | None:
        if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            raise CannotCreateGroupError()
        existing_group = await self.repo.get_by_name(name)
        if existing_group:
            raise GroupAlreadyExistsError(name)
        group = Group(name=name)
        created_group = await self.repo.add(group)
        if not created_group:
            return None

        return self._to_group_read_dto(created_group)


class EditGroup(UseCaseBase):
    def __init__(self, repo: IGroupRepository):
        self.repo = repo

    async def execute(
        self, group_id: UUID, data: GroupEditDTO, current_user: DataFromTokenDTO
    ) -> GroupReadDTO:
        if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            raise CannotEditGroupError()
        if data.name:
            existing_group = await self.repo.get_by_name(data.name)
            if existing_group:
                raise GroupAlreadyExistsError(data.name)
        group = await self.repo.get_by_id(ID(group_id))
        if not group:
            raise GroupNotFoundError()
        edited_group = await self.repo.update(ID(group_id), data)
        if not edited_group:
            raise GroupNotFoundError()
        return self._to_group_read_dto(edited_group)


class DeleteGroup(UseCaseBase):
    def __init__(self, repo: IGroupRepository):
        self.repo = repo

    async def execute(
        self, group_id: UUID, сurrent_user: DataFromTokenDTO
    ) -> GroupReadDTO:
        if сurrent_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            raise CannotDeleteGroupError()
        group = await self.repo.get_by_id(ID(group_id))
        if not group:
            raise GroupNotFoundError()
        deleted_group = await self.repo.delete(ID(group_id))
        if not deleted_group:
            raise GroupNotFoundError()
        return self._to_group_read_dto(deleted_group)


class AddUserToGroup(UseCaseBase):
    def __init__(self, repo: IGroupRepository):
        self.repo = repo

    async def execute(
        self, group_id: UUID, user_id: UUID, current_user: DataFromTokenDTO
    ) -> None:
        if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            raise CannotAddUserToGroupError()

        group = await self.repo.get_by_id(ID(group_id))
        if not group:
            raise GroupNotFoundError()

        status = await self.repo.is_user_in_group(ID(group_id), ID(user_id))

        if status is None:
            raise UserNotFoundError()

        await self.repo.add_user_to_group(ID(group_id), ID(user_id))


class RemoveUserFromGroup(UseCaseBase):
    def __init__(self, repo: IGroupRepository):
        self.repo = repo

    async def execute(
        self, group_id: UUID, user_id: UUID, current_user: DataFromTokenDTO
    ) -> None:
        if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            raise CannotRemoveUserFromGroupError()

        group = await self.repo.get_by_id(ID(group_id))
        if not group:
            raise GroupNotFoundError()

        status = await self.repo.is_user_in_group(ID(group_id), ID(user_id))

        if status is None:
            raise UserNotFoundError()

        await self.repo.delete_user_from_group(ID(group_id), ID(user_id))


class GetUsersInGroup(UseCaseBase):
    def __init__(self, repo: IGroupRepository):
        self.repo = repo

    async def execute(
        self, group_id: UUID, current_user: DataFromTokenDTO
    ) -> List[UserReadDTO]:
        is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        is_moderator = current_user.role == UserRole.MODERATOR
        group = await self.repo.get_by_id(ID(group_id))
        if not group:
            raise GroupNotFoundError()
        if not (is_admin or is_moderator):
            raise CannotGetGroupUsersError()
        if is_moderator and str(current_user.group_id) != str(group_id):
            raise CannotGetGroupUsersError()

        users = await self.repo.get_users_in_group(ID(group_id))

        return [self._to_user_read_dto(user) for user in users]
