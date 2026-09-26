from source.application.interfaces import IUserRepository
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


class FakeUserRepository(IUserRepository):
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
            self.users[user_id] = user
            return user

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
