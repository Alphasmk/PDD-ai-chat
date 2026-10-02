from uuid import UUID
from dataclasses import dataclass, field
from src.domain.entities import Entity
from src.domain.enums import RuleType
from datetime import datetime, timezone
from typing import Dict, Optional

@dataclass(kw_only=True, frozen=True)
class TrafficRule(Entity):
    id: UUID
    rule_id: str
    title: str
    section: Optional[str] = None
    type: RuleType = RuleType.RULE
    name: Optional[str] = None
    text: str
    image_path: Optional[str] = None
