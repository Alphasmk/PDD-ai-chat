from dataclasses import dataclass
from uuid import UUID
from source.domain.entities.user import UserEntity
from source.domain.value_objects.user_role import UserRole


@dataclass(frozen=True, slots=True, kw_only=True)
class AdminUserDTO:
    id: UUID
    name: str
    surname: str
    username: str
    email: str
    role: UserRole
    is_blocked: bool
    is_superadmin: bool

    @classmethod
    def from_user(cls, user: UserEntity) -> "AdminUserDTO":
        return cls(
            id=user.id.value,
            name=user.name.value,
            surname=user.surname.value,
            username=user.username,
            email=user.email.value,
            role=user.role,
            is_blocked=user.is_blocked,
            is_superadmin=user.is_superadmin,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class UserPageDTO:
    items: list[AdminUserDTO]
    limit: int
    offset: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeRoleDTO:
    id: UUID
    role: UserRole
    is_blocked: bool
    is_superadmin: bool
