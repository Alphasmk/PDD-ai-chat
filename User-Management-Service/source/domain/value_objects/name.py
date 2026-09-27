"""Name dataclass definition"""

import re
from dataclasses import dataclass
from typing import ClassVar
from source.domain.exceptions import NameLengthError, NamePatternError


@dataclass(frozen=True)
class Name:
    """Data class for name"""

    value: str

    MIN_LEN: ClassVar[int] = 2
    MAX_LEN: ClassVar[int] = 20
    PATTERN: ClassVar[str] = r"^[a-zA-Zа-яА-ЯёЁ\-']+$"

    @classmethod
    def validate_name(cls, name: str) -> None:
        """Validate name"""
        if not cls.MIN_LEN <= len(name) <= cls.MAX_LEN:
            raise NameLengthError(name, cls.MAX_LEN, cls.MIN_LEN)
        if re.match(cls.PATTERN, name) is None:
            raise NamePatternError(name)

    @classmethod
    def from_trusted(cls, name: str) -> "Name":
        instance = object.__new__(cls)
        object.__setattr__(instance, "value", name)
        return instance

    def __post_init__(self) -> None:
        self.validate_name(self.value)
