"""User model definition"""

import datetime
import uuid
from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from source.infrastructure.database.models import Base
from source.domain.enums.user_role import UserRole

if TYPE_CHECKING:
    from source.infrastructure.database.models import Group


class User(Base):
    """User model class"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    surname: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(nullable=True, unique=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"), nullable=True
    )
    group: Mapped[Optional["Group"]] = relationship(
        "Group", back_populates="users", lazy="selectin"
    )
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    image_s3_path: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    # pylint: disable=not-callable
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=None, onupdate=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"User\n{self.id=}\n{self.name=}\n{self.surname=}\n"
            + f"{self.username=}\n{self.email=}\n{self.group=}\n"
            + f"{self.role=}\n{self.created_at=}\n{self.updated_at=}"
        )
