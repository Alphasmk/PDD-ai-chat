from uuid import UUID
from dataclasses import dataclass, field
from src.domain.entities import Entity
from src.domain.enums import RuleType
from datetime import datetime, timezone
from typing import List

@dataclass(kw_only=True, frozen=True)
class TrafficRuleChunk(Entity):
    rule_id: str
    search_text: str
    embedding: List[float] = field(default_factory=list)
