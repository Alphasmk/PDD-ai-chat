from source.application.exceptions.base import ApplicationException
from source.domain.exceptions.user_access_exceptions import (
    Forbidden,
    UserBlocked,
    ProtectedAccount,
    InvalidTargetState,
)


class ForbiddenError(ApplicationException):
    def __init__(self) -> None:
        super().__init__("forbidden")


class UserBlockedError(ApplicationException):
    def __init__(self) -> None:
        super().__init__("user_blocked")


class ProtectedAccountError(ApplicationException):
    def __init__(self) -> None:
        super().__init__("protected_account")


class InvalidTargetStateError(ApplicationException):
    def __init__(self) -> None:
        super().__init__("invalid_target_state")


class ServiceUnavailableError(ApplicationException):
    def __init__(self) -> None:
        super().__init__("service_unavailable")


def access_error(
    error: Forbidden | UserBlocked | ProtectedAccount | InvalidTargetState,
) -> ApplicationException:
    if isinstance(error, Forbidden):
        return ForbiddenError()
    if isinstance(error, UserBlocked):
        return UserBlockedError()
    if isinstance(error, ProtectedAccount):
        return ProtectedAccountError()
    return InvalidTargetStateError()


class UsernameTakenError(ApplicationException):
    def __init__(self, username: str) -> None:
        message = f"User with username '{username}' already exists"
        super().__init__(message)


class EmailTakenError(ApplicationException):
    def __init__(self, email: str) -> None:
        message = f"User with email '{email}' already exists"
        super().__init__(message)


class PhoneNumberTaken(ApplicationException):
    def __init__(self, phone: str) -> None:
        message = f"User with phone number '{phone}' already exists"
        super().__init__(message)


class UserNotFoundError(ApplicationException):
    def __init__(self) -> None:
        message = "User not found"
        super().__init__(message)


class InvalidCredentialsError(ApplicationException):
    def __init__(self) -> None:
        message = "Incorrect username or password"
        super().__init__(message)
