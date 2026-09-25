from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import datetime


@dataclass(frozen=True, slots=False, kw_only=True)
class GroupReadDTO:
    id: UUID
    name: str
    created_at: datetime


@dataclass(frozen=True, slots=False, kw_only=True)
class GroupEditDTO:
    name: Optional[str] = None
