from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, repr=False)
class TokenDTO:
    access: str
    refresh: str
    token_type: str = "bearer"


@dataclass(frozen=True, repr=False)
class DataFromTokenDTO:
    user_id: UUID
    email: str
    role: str
    group_id: UUID | None = None
