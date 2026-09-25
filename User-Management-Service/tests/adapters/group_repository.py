from typing import List
from dataclasses import replace
from source.application.interfaces import IGroupRepository
from source.domain.entities.user import UserEntity
from source.domain.entities.group import GroupEntity
from source.application.dto import GroupEditDTO
from source.domain.value_objects import ID


class FakeGroupRepository(IGroupRepository):
    def __init__(self, users_data: dict[str, UserEntity] | None = None):
        self.groups: dict[str, GroupEntity] = {}
        self.users: dict[str, UserEntity] = users_data if users_data is not None else {}

    async def get_by_id(self, group_id: ID) -> GroupEntity | None:
        return self.groups.get(str(group_id.value))

    async def get_by_name(self, name: str) -> GroupEntity | None:
        for group in self.groups.values():
            if group.name == name:
                return group
        return None

    async def add(self, group: GroupEntity) -> GroupEntity | None:
        if not group:
            return None
        self.groups[str(group.id.value)] = group
        return group

    async def update(self, group_id: ID, data: GroupEditDTO) -> GroupEntity | None:
        group_id_str = str(group_id.value)
        group = self.groups.get(group_id_str)

        if not group:
            return None

        if data.name is not None:
            group = replace(group, name=data.name)
            self.groups[group_id_str] = group

        return group

    async def delete(self, group_id: ID) -> GroupEntity | None:
        return self.groups.pop(str(group_id.value), None)

    async def add_user_to_group(self, group_id: ID, user_id: ID) -> None:
        user_id_str = str(user_id.value)
        user = self.users.get(user_id_str)

        if user:
            self.users[user_id_str] = replace(user, group_id=group_id.value)

    async def is_user_in_group(self, group_id: ID, user_id: ID) -> bool | None:
        user_id_str = str(user_id.value)
        user = self.users.get(user_id_str)

        if not user:
            return None

        if user.group_id is None:
            return False

        u_group_id = (
            user.group_id.value if hasattr(user.group_id, "value") else user.group_id
        )
        return str(u_group_id) == str(group_id.value) and user.group_id is not None

    async def delete_user_from_group(self, group_id: ID, user_id: ID) -> None:
        user_id_str = str(user_id.value)
        user = self.users.get(user_id_str)

        if user and user.group_id:
            u_group_id = (
                user.group_id.value
                if hasattr(user.group_id, "value")
                else user.group_id
            )
            if str(u_group_id) == str(group_id.value):
                self.users[user_id_str] = replace(user, group_id=None)

    async def get_users_in_group(self, group_id: ID) -> List[UserEntity]:
        users_in_group = []
        for user in self.users.values():
            if user.group_id:
                u_group_id = (
                    user.group_id.value
                    if hasattr(user.group_id, "value")
                    else user.group_id
                )
                if str(u_group_id) == str(group_id.value):
                    users_in_group.append(user)

        return users_in_group
