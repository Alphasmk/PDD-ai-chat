from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint, Index, text, ForeignKey
from source.infrastructure.database.models.roles import Role
from source.infrastructure.database.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role_id IN (1, 2)", name="users_role_id_check"),
        CheckConstraint(
            "NOT is_blocked OR role_id = 1", name="users_blocked_role_check"
        ),
        CheckConstraint(
            "NOT is_superadmin OR role_id = 2", name="users_superadmin_role_check"
        ),
        Index(
            "ux_users_superadmin",
            "is_superadmin",
            unique=True,
            postgresql_where=text("is_superadmin"),
            sqlite_where=text("is_superadmin"),
        ),
        Index("ix_users_created_at_id", "created_at", "id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    surname: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    phone_number: Mapped[str | None] = mapped_column(nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=func.now(), nullable=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", name="users_role_id_fkey", ondelete="RESTRICT"),
        nullable=False,
        server_default=text("1"),
        default=1,
    )
    role: Mapped[Role] = relationship(lazy="raise")
    is_superadmin: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false"), default=False
    )
    is_blocked: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false"), default=False
    )
