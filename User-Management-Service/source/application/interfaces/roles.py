from abc import ABC, abstractmethod
from source.domain.entities.role import RoleEntity


class IRoleRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[RoleEntity]: ...
