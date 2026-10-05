from uuid import UUID
from dataclasses import dataclass, field
from src.domain.entities import Entity
from src.domain.enums import ChatRole
from datetime import datetime, timezone
from typing import Dict, Optional

@dataclass(kw_only=True, frozen=True)
class Message(Entity):
    chat_id: UUID
    role: ChatRole = ChatRole.USER
    content: str
    image_context: Dict = field(default_factory=dict)
    model: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
