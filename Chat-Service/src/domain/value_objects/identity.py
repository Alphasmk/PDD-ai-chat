"""Identifier dataclass definition"""

from dataclasses import dataclass, field
from uuid import UUID, uuid7


@dataclass(frozen=True)
class ID:
    """Class definition to objects indentifier"""

    value: UUID = field(default_factory=uuid7)