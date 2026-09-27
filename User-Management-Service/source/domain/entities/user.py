"""Definition of the user entity class"""

from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field, replace
from source.domain.entities.base import Entity

from source.domain.value_objects import PasswordHash, Email, Name
from source.domain.value_objects.user_role import UserRole
from source.domain.exceptions.user_access_exceptions import (
    InvalidTargetState,
    ProtectedAccount,
)


@dataclass(frozen=True, kw_only=True)
class UserEntity(Entity):
    """User entity class"""

    name: Name
    surname: Name
    username: str
    password_hash: PasswordHash
    phone_number: Optional[str] = None
    email: Email
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    role: UserRole = UserRole.USER
    is_blocked: bool = False
    is_superadmin: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.role, UserRole)
            or type(self.is_blocked) is not bool
            or type(self.is_superadmin) is not bool
        ):
            raise InvalidTargetState()
        if self.is_blocked and self.role is not UserRole.USER:
            raise InvalidTargetState()
        if self.is_superadmin and self.role is not UserRole.ADMIN:
            raise InvalidTargetState()

    def change_role(self, role: UserRole) -> "UserEntity":
        if self.is_superadmin:
            raise ProtectedAccount()
        if self.is_blocked and role is UserRole.ADMIN:
            raise InvalidTargetState()
        if role is self.role:
            return self
        return replace(self, role=role, updated_at=datetime.now(timezone.utc))

    def block(self) -> "UserEntity":
        if self.is_superadmin:
            raise ProtectedAccount()
        if self.role is UserRole.ADMIN:
            raise InvalidTargetState()
        if self.is_blocked:
            return self
        return replace(self, is_blocked=True, updated_at=datetime.now(timezone.utc))

    def ensure_deletable(self) -> None:
        if self.is_superadmin:
            raise ProtectedAccount()
