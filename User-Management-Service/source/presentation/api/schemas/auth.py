from datetime import datetime
from uuid import UUID
from pydantic import EmailStr
from source.presentation.api.schemas.base import Base


class UserResponse(Base):
    id: UUID
    name: str
    surname: str
    username: str
    email: EmailStr
    created_at: datetime
    phone_number: str | None = None
    image_s3_path: str | None = None
    updated_at: datetime | None = None


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
