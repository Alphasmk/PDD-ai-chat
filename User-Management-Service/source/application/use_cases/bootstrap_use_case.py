from collections.abc import Callable
from dataclasses import dataclass, field
from source.application.interfaces.bootstrap import IBootstrapRepository
from source.application.exceptions import UsernameTakenError, EmailTakenError
from source.domain.entities.user import UserEntity
from source.domain.interfaces import IPasswordHasher
from source.domain.value_objects import Name, Email, RawPassword
from source.domain.value_objects.user_role import UserRole
from source.domain.exceptions.base import DomainTypeError


class InitializationError(Exception):
    pass


@dataclass(frozen=True, kw_only=True)
class BootstrapData:
    username: str
    email: str
    password: str = field(repr=False)
    name: str
    surname: str


class BootstrapSuperadmin:
    def __init__(
        self, repository: IBootstrapRepository, hasher: IPasswordHasher
    ) -> None:
        self.repository = repository
        self.hasher = hasher

    async def execute(self, initial: Callable[[], BootstrapData]) -> bool:
        if await self.repository.get_superadmin() is not None:
            return False
        data = initial()
        try:
            if not data.username.strip():
                raise InitializationError("invalid_initial_data")
            name, surname, email, password = (
                Name(data.name),
                Name(data.surname),
                Email(data.email),
                RawPassword(data.password),
            )
        except DomainTypeError as error:
            raise InitializationError("invalid_initial_data") from error
        if (
            await self.repository.get_by_username(data.username) is not None
            or await self.repository.get_by_email(email) is not None
        ):
            raise InitializationError("identity_conflict")
        user = UserEntity(
            name=name,
            surname=surname,
            username=data.username,
            email=email,
            password_hash=await self.hasher.hash(password),
            role=UserRole.ADMIN,
            is_superadmin=True,
        )
        try:
            await self.repository.add(user)
        except (UsernameTakenError, EmailTakenError) as error:
            raise InitializationError("identity_conflict") from error
        return True
