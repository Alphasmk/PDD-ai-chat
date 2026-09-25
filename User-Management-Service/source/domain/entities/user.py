"""Definition of the user entity class"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field
from source.domain.enums.user_role import UserRole
from source.domain.entities.base import Entity

from source.domain.value_objects import PasswordHash, Email, Name


@dataclass(frozen=True, kw_only=True)
class UserEntity(Entity):
    """User entity class"""

    name: Name
    surname: Name
    username: str
    password_hash: PasswordHash
    phone_number: Optional[str] = None
    email: Email
    role: UserRole = UserRole.USER
    image_s3_path: Optional[str] = None
    is_blocked: bool = False
    group_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
