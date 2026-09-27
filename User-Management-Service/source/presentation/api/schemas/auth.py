from datetime import datetime
from uuid import UUID
from pydantic import EmailStr
from source.presentation.api.schemas.base import Base
from source.domain.value_objects.user_role import UserRole


class UserResponse(Base):
    id: UUID
    name: str
    surname: str
    username: str
    email: EmailStr
    created_at: datetime
    phone_number: str | None = None
    updated_at: datetime | None = None
    role: UserRole
    is_blocked: bool
    is_superadmin: bool


class UserSignupRequest(Base):
    name: str
    surname: str
    username: str
    password: str
    email: EmailStr
    phone_number: str | None = None


class TokenResponse(Base):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ResetPasswordRequest(Base):
    email: EmailStr


class ResetPasswordResponse(Base):
    message: str
