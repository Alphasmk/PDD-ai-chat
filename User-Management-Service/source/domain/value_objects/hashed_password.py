"""Password hash dataclass definition"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PasswordHash:
    """Data class for pasword hash"""

    value: str = field(repr=False)
