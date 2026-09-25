from abc import abstractmethod, ABC
from source.domain.value_objects import PasswordHash, RawPassword


class IPasswordHasher(ABC):
    @abstractmethod
    async def hash(self, password: RawPassword) -> PasswordHash: ...

    @abstractmethod
    async def verify(self, raw_password: str, password_hash: str) -> bool: ...
