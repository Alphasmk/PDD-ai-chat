from source.application.exceptions.base import ApplicationException


class TokenExpiredError(ApplicationException):
    def __init__(self) -> None:
        message = "Token has expired"
        super().__init__(message)


class InvalidTokenError(ApplicationException):
    def __init__(self) -> None:
        message = "Invalid token"
        super().__init__(message)


class MissingTokenError(ApplicationException):
    def __init__(self) -> None:
        message = "Refresh token is missing"
        super().__init__(message)


class TokenRevokedError(ApplicationException):
    def __init__(self) -> None:
        message = "Refresh token is revoked"
        super().__init__(message)
