"""Email errors"""

from source.domain.exceptions.base import DomainTypeError


class EmailPatternError(DomainTypeError):
    def __init__(self, email: str):
        message = f"The mail '{email}' is in an invalid format"
        super().__init__((message))
