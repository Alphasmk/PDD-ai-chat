"""Password dataclass definition"""

import re
from dataclasses import dataclass, field
from typing import ClassVar
from source.domain.exceptions import (
    PasswordLengthError,
    PasswordPatternError,
)


@dataclass(frozen=True)
class RawPassword:
    """Data class for password"""

    value: str = field(repr=False)

    MIN_LEN: ClassVar[int] = 8
    MAX_LEN: ClassVar[int] = 20
    PATTERN: ClassVar[str] = r"[A-Za-z0-9@#$%^&+=]+$"

    @classmethod
    def validate_password(cls, password: str) -> None:
        """Validate password"""
        if not cls.MIN_LEN <= len(password) <= cls.MAX_LEN:
            raise PasswordLengthError(cls.MAX_LEN, cls.MIN_LEN)
        if re.match(cls.PATTERN, password) is None:
            raise PasswordPatternError()

    def __post_init__(self) -> None:
        self.validate_password(self.value)
