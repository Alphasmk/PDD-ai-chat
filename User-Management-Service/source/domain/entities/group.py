"""Definition of the group entity class"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from source.domain.entities.base import Entity


@dataclass(frozen=True, kw_only=True)
class GroupEntity(Entity):
    """Group entity class"""

    name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
