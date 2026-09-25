from typing import List
from dataclasses import replace
from source.application.interfaces import IUserRepository
from source.domain.entities.user import UserEntity
from source.application.dto import UserPaginationDTO
from source.domain.enums.user_role import UserRole
from source.domain.value_objects import (
    ID,
    Email,
)
from source.application.exceptions import (
    EmailTakenError,
    UsernameTakenError,
    PhoneNumberTaken,
)


class FakeUserRepository(IUserRepository):
    def __init__(self) -> None:
        self.users: dict[str, UserEntity] = {}

    async def get_by_id(self, user_id: ID) -> UserEntity | None:
        return self.users.get(str(user_id.value))

    async def update(self, user: UserEntity) -> UserEntity | None:
        if not user:
            return None

        for existing_user in self.users.values():
            if existing_user.id.value != user.id.value:
                if existing_user.email.value == user.email.value:
                    raise EmailTakenError(user.email.value)
                if existing_user.username == user.username:
                    raise UsernameTakenError(user.username)
                if (
                    existing_user.phone_number == user.phone_number
                    and user.phone_number is not None
                ):
                    raise PhoneNumberTaken(user.phone_number)

        user_id = str(user.id.value)
        if user_id in self.users:
            self.users[user_id] = user
            return user

        return None

    async def add(self, user: UserEntity) -> UserEntity | None:
        if not user:
            return None
        for existing_user in self.users.values():
            if existing_user.email.value == user.email.value:
                raise EmailTakenError(user.email.value)
            if existing_user.username == user.username:
                raise UsernameTakenError(user.username)
            if (
                existing_user.phone_number == user.phone_number
                and user.phone_number is not None
            ):
                raise PhoneNumberTaken(user.phone_number)
        self.users[str(user.id.value)] = user
        return user

    async def delete(self, user: UserEntity) -> None:
        self.users.pop(str(user.id.value), None)

    async def get_by_email(self, user_email: Email) -> UserEntity | None:
        for user in self.users.values():
            if user.email == user_email:
                return user
        return None

    async def get_by_username(self, username: str) -> UserEntity | None:
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    async def get_users(self, params: UserPaginationDTO) -> List[UserEntity]:
        all_users = list(self.users.values())

        if params.filter_by_name:
            search_term = params.filter_by_name.lower()
            filtered_users = []
            for user in all_users:
                name_str = user.name.value if user.name else ""
                surname_str = user.surname.value if user.surname else ""

                name_match = search_term in name_str.lower()
                surname_match = search_term in surname_str.lower()
                if name_match or surname_match:
                    filtered_users.append(user)
            all_users = filtered_users

        if hasattr(params, "group") and params.group:
            expected_group = (
                params.group.value if hasattr(params.group, "value") else params.group
            )

            filtered_by_group = []
            for user in all_users:
                if user.group_id is None:
                    continue
                u_group_id = (
                    user.group_id.value
                    if hasattr(user.group_id, "value")
                    else user.group_id
                )
                if str(u_group_id) == str(expected_group):
                    filtered_by_group.append(user)
            all_users = filtered_by_group

        sort_field = params.sort_by if params.sort_by else "created_at"
        is_desc = params.order_by == "desc"

        def get_sort_value(user: UserEntity):
            val = getattr(user, sort_field, getattr(user, "created_at", ""))
            return val if val is not None else ""

        all_users.sort(key=get_sort_value, reverse=is_desc)

        offset = (params.page - 1) * params.limit
        paginated_users = all_users[offset : offset + params.limit]

        return paginated_users

    async def change_block_state(self, user_id: ID) -> bool | None:
        if str(user_id.value) in self.users:
            state = not self.users[str(user_id.value)].is_blocked
            self.users[str(user_id.value)] = replace(
                self.users[str(user_id.value)], is_blocked=state
            )
            return True
        return False

    async def change_role(self, user_id: ID, role: UserRole) -> None:
        if str(user_id.value) in self.users:
            self.users[str(user_id.value)] = replace(
                self.users[str(user_id.value)], role=role
            )
