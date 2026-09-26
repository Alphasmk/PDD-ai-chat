from uuid import UUID
from pydantic import EmailStr
from source.presentation.api.schemas.base import Base


class UserDeleteResponse(Base):
    id: UUID
    username: str
    email: EmailStr


class UserEditRequest(Base):
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None


class UserEditResponse(Base):
    name: str
    surname: str
    username: str
    email: EmailStr
    phone_number: str | None = None
    image_s3_path: str | None = None


class ImageResponse(Base):
    image_url: str


class ImageUploadResponse(Base):
    image_s3_path: str
