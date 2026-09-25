from uuid import UUID
from pydantic import EmailStr
from typing import Optional, Literal
from source.domain.enums.user_role import UserRole
from source.presentation.api.schemas.base import Base


class UserDeleteResponse(Base):
    id: UUID
    username: str
    email: EmailStr


class UserEditRequest(Base):
    name: Optional[str] = None
    surname: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    image_s3_path: Optional[str] = None


class UserEditResponse(Base):
    name: str
    surname: str
    username: str
    email: EmailStr
    phone_number: Optional[str] = None
    image_s3_path: Optional[str] = None


class UserPaginationRequest(Base):
    limit: int
    page: int
    filter_by_name: Optional[str] = None
    sort_by: Optional[str] = None
    order_by: Literal["asc", "desc"] = "asc"


class ChangeRoleRequest(Base):
    role: UserRole


class MessageResponse(Base):
    message: str


class ImageResponse(Base):
    image_url: str


class ImageUploadResponse(Base):
    image_s3_path: str
