"""Email dataclass definition"""

import re
from dataclasses import dataclass
from typing import ClassVar
from source.domain.exceptions import EmailPatternError


@dataclass(frozen=True)
class Email:
    """Data class for email"""

    value: str

    PATTERN: ClassVar[str] = r"^\S+@\S+\.\S+$"

    @classmethod
    def validate_email(cls, email: str) -> None:
        """Validate email"""
        if re.match(cls.PATTERN, email) is None:
            raise EmailPatternError(email)

    @classmethod
    def from_trusted(cls, email: str) -> "Email":
        instance = object.__new__(cls)
        object.__setattr__(instance, "value", email)
        return instance

    def __post_init__(self) -> None:
        self.validate_email(self.value)
