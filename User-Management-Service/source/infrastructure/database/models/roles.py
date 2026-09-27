from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from source.infrastructure.database.models.base import Base


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint(
            "(id = 1 AND value = 'user') OR (id = 2 AND value = 'admin')",
            name="roles_catalog_check",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    value: Mapped[str] = mapped_column(nullable=False, unique=True)
    label: Mapped[str] = mapped_column(nullable=False)
