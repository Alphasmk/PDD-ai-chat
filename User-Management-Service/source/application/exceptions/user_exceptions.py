from source.application.exceptions.base import ApplicationException


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


class ActionNotAllowedError(ApplicationException):
    def __init__(self, err) -> None:
        message = f"Action not allowed: {err}"
        super().__init__(message)


class UserEditNotAllowedError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot edit this user"
        super().__init__(message)


class UserGetInfoNotAllowed(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot get info about users"
        super().__init__(message)


class ModeratorGetInfoNotAllowed(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot receive information about users not from your group"
        super().__init__(message)


class InvalidCredentialsError(ApplicationException):
    def __init__(self) -> None:
        message = "Incorrect username or password"
        super().__init__(message)


class CannotChangeImageError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot change custom images other than your own"
        super().__init__(message)


class UploadImageError(ApplicationException):
    def __init__(self) -> None:
        message = "Error when uploading an image"
        super().__init__(message)


class DeleteImageError(ApplicationException):
    def __init__(self) -> None:
        message = "Error when deleting an image"
        super().__init__(message)


class UserHasNoImageError(ApplicationException):
    def __init__(self, username: str) -> None:
        message = f"User {username} has no image"
        super().__init__(message)


class ImageReceivingError(ApplicationException):
    def __init__(self) -> None:
        message = "Error loading image"
        super().__init__(message)


class CannotDeleteImageError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot delete custom images other than your own"
        super().__init__(message)
