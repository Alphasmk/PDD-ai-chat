from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from source.domain.value_objects.user_role import UserRole


@dataclass(frozen=True, slots=True, kw_only=True)
class UserCreateDTO:
    name: str
    surname: str
    username: str
    password: str
    email: str
    phone_number: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateUserDTO:
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    email: str | None = None
    phone_number: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UserReadDTO:
    id: UUID
    name: str
    surname: str
    username: str
    email: str
    created_at: datetime
    phone_number: str | None = None
    updated_at: datetime | None = None
    role: UserRole = UserRole.USER
    is_blocked: bool = False
    is_superadmin: bool = False
