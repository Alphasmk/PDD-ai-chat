from typing import Optional
from pydantic import EmailStr
from datetime import datetime
from source.domain.enums.user_role import UserRole
from source.presentation.api.schemas.base import Base
from uuid import UUID


class UserResponse(Base):
    id: UUID
    name: str
    surname: str
    username: str
    email: EmailStr
    phone_number: Optional[str] = None
    role: UserRole
    is_blocked: bool
    image_s3_path: Optional[str] = None
    group_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserSignupRequest(Base):
    """User registration schema"""

    name: str
    surname: str
    username: str
    password: str
    email: EmailStr
    phone_number: Optional[str] = None


class TokenResponse(Base):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class DataFromTokenResponse(Base):
    user_id: UUID
    email: str
    role: str
    group_id: Optional[UUID] = None


class ResetPasswordRequest(Base):
    email: EmailStr


class ResetPasswordResponse(Base):
    message: str
