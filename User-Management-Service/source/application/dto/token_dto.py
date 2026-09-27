from dataclasses import dataclass
from uuid import UUID
from typing import TypedDict


class AccessPayload(TypedDict):
    sub: str
    email: str


class RefreshPayload(TypedDict):
    sub: str


@dataclass(frozen=True, repr=False)
class TokenDTO:
    access: str
    refresh: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class DataFromTokenDTO:
    """Subject resolved from a verified access token to an existing account."""

    user_id: UUID
    email: str
