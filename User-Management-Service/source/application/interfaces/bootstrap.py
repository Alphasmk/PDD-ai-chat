from abc import ABC, abstractmethod
from source.domain.entities.user import UserEntity
from source.domain.value_objects import Email


class IBootstrapRepository(ABC):
    @abstractmethod
    async def get_superadmin(self) -> UserEntity | None: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> UserEntity | None: ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> UserEntity | None: ...

    @abstractmethod
    async def add(self, user: UserEntity) -> UserEntity: ...
