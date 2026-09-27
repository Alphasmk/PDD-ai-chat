from source.application.interfaces import IUserRepository
from source.application.interfaces.bootstrap import IBootstrapRepository

from dataclasses import replace
from datetime import datetime, timezone
from source.domain.entities.user import UserEntity
from source.domain.value_objects import (
    ID,
    Email,
)
from source.application.exceptions import (
    EmailTakenError,
    UsernameTakenError,
    PhoneNumberTaken,
)


class FakeUserRepository(IUserRepository, IBootstrapRepository):
    def __init__(self) -> None:
        self.users: dict[str, UserEntity] = {}

    async def get_by_id(self, user_id: ID) -> UserEntity | None:
        return self.users.get(str(user_id.value))

    async def update(self, user: UserEntity) -> UserEntity | None:

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
            current = self.users[user_id]
            saved = replace(
                user,
                role=current.role,
                is_blocked=current.is_blocked,
                is_superadmin=current.is_superadmin,
                updated_at=datetime.now(timezone.utc),
            )
            self.users[user_id] = saved
            return saved

        return None

    async def add(self, user: UserEntity) -> UserEntity:
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

    async def get_for_update(self, user_id: ID) -> UserEntity | None:
        return await self.get_by_id(user_id)

    async def get_superadmin(self) -> UserEntity | None:
        return next(
            (user for user in self.users.values() if user.is_superadmin),
            None,
        )

    async def list_page(self, limit: int, offset: int) -> list[UserEntity]:
        return sorted(
            self.users.values(), key=lambda user: (user.created_at, user.id.value)
        )[offset : offset + limit]

    async def set_role(self, user: UserEntity) -> UserEntity:
        key = str(user.id.value)
        saved = replace(self.users[key], role=user.role, updated_at=user.updated_at)
        self.users[key] = saved
        return saved

    async def set_blocked(self, user: UserEntity) -> UserEntity:
        key = str(user.id.value)
        saved = replace(
            self.users[key], is_blocked=user.is_blocked, updated_at=user.updated_at
        )
        self.users[key] = saved
        return saved
