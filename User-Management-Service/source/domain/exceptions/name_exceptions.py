"""Name errors"""

from source.domain.exceptions.base import DomainTypeError


class NameLengthError(DomainTypeError):
    def __init__(self, name: str, max_len: int, min_len: int):
        message = (
            f"The name '{name}' has an invalid length(max: {max_len}, min: {min_len})."
        )
        super().__init__(message)


class NamePatternError(DomainTypeError):
    def __init__(self, name: str):
        message = f"The name '{name}' has an invalid pattern."
        super().__init__(message)
