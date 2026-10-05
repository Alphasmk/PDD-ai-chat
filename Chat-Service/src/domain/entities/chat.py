from uuid import UUID
from dataclasses import dataclass, field
from src.domain.entities import Entity
from datetime import datetime, timezone
from typing import Optional

@dataclass(kw_only=True, frozen=True)
class Chat(Entity):
    user_id: UUID
    title: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None