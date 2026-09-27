from typing import Literal
from uuid import UUID
from pydantic import ConfigDict, EmailStr
from source.domain.value_objects.user_role import UserRole
from source.presentation.api.schemas.base import Base


class ChangeRoleRequest(Base):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "admin"]


class ChangeRoleResponse(Base):
    id: UUID
    role: UserRole
    is_blocked: bool
    is_superadmin: bool


class AdminUserResponse(Base):
    id: UUID
    name: str
    surname: str
    username: str
    email: EmailStr
    role: UserRole
    is_blocked: bool
    is_superadmin: bool


class UserPageResponse(Base):
    items: list[AdminUserResponse]
    limit: int
    offset: int
