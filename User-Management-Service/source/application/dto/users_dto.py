from dataclasses import dataclass
from uuid import UUID
from typing import Optional, Literal
from datetime import datetime

from source.domain.enums.user_role import UserRole


@dataclass(frozen=True, slots=True, kw_only=True)
class UserCreateDTO:
    name: str
    surname: str
    username: str
    password: str
    email: str
    image_s3_path: Optional[str] = None
    phone_number: Optional[str] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateUserDTO:
    name: Optional[str] = None
    surname: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    image_s3_path: Optional[str] = None
    phone_number: Optional[str] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UserReadDTO:
    id: UUID
    name: str
    surname: str
    username: str
    email: str
    phone_number: Optional[str] = None
    role: UserRole
    image_s3_path: Optional[str] = None
    is_blocked: bool = False
    group_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass(frozen=True, slots=False, kw_only=True)
class UserPaginationDTO:
    limit: int
    page: int
    filter_by_name: Optional[str] = None
    sort_by: Optional[str] = None
    order_by: Literal["asc", "desc"] = "asc"
    group: Optional[UUID] = None


@dataclass(frozen=True, slots=False, kw_only=True)
class UserRoleChangeDTO:
    role: UserRole
