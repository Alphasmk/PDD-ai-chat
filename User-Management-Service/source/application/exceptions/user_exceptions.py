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


class InvalidCredentialsError(ApplicationException):
    def __init__(self) -> None:
        message = "Incorrect username or password"
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
