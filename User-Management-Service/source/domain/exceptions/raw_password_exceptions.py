"""Raw password errors"""

from source.domain.exceptions.base import DomainTypeError


class PasswordLengthError(DomainTypeError):
    def __init__(self, max_len: int, min_len: int):
        message = f"The password has an invalid length(max: {max_len}, min: {min_len})."
        super().__init__(message)


class PasswordPatternError(DomainTypeError):
    def __init__(self):
        message = "The password has an invalid pattern"
        super().__init__(message)
