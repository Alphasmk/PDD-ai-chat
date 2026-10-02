from uuid import UUID
from pydantic import EmailStr
from source.presentation.api.schemas.base import Base
from source.domain.value_objects.user_role import UserRole


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
    role: UserRole
    is_blocked: bool
    is_superadmin: bool
