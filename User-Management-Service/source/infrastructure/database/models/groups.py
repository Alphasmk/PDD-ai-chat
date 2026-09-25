"""Group model definition"""

import datetime
import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from source.infrastructure.database.models import Base

if TYPE_CHECKING:
    from source.infrastructure.database.models import User


class Group(Base):
    """Group model class"""

    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    # pylint: disable=not-callable
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="group", lazy="select"
    )

    def __repr__(self) -> str:
        return f"Group:{self.id=}:{self.name=}:{self.created_at=}"
