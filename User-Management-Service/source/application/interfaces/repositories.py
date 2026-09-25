from typing import List
from abc import abstractmethod, ABC

from source.domain.value_objects import Email, ID

from source.domain.entities.user import UserEntity as User
from source.domain.entities.group import GroupEntity as Group
from source.domain.enums.user_role import UserRole
from source.application.dto.users_dto import UserPaginationDTO
from source.application.dto.groups_dto import GroupEditDTO


class IUserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> User | None: ...

    @abstractmethod
    async def update(self, user: User) -> User | None: ...

    @abstractmethod
    async def delete(self, user: User) -> None: ...

    @abstractmethod
    async def get_by_id(self, user_id: ID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, user_email: Email) -> User | None: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def get_users(self, params: UserPaginationDTO) -> List[User]: ...

    @abstractmethod
    async def change_block_state(self, user_id: ID) -> bool | None: ...

    @abstractmethod
    async def change_role(self, user_id: ID, role: UserRole) -> UserRole | None: ...


class IGroupRepository(ABC):
    @abstractmethod
    async def get_by_id(self, group_id: ID) -> Group | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Group | None: ...

    @abstractmethod
    async def add(self, group: Group) -> Group | None: ...

    @abstractmethod
    async def update(self, group_id: ID, data: GroupEditDTO) -> Group | None: ...

    @abstractmethod
    async def delete(self, group_id: ID) -> Group | None: ...

    @abstractmethod
    async def add_user_to_group(self, group_id: ID, user_id: ID) -> None: ...

    @abstractmethod
    async def is_user_in_group(self, group_id: ID, user_id: ID) -> bool | None: ...

    @abstractmethod
    async def delete_user_from_group(self, group_id: ID, user_id: ID) -> None: ...

    @abstractmethod
    async def get_users_in_group(self, group_id: ID) -> List[User]: ...
