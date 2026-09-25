from source.domain.exceptions.base import DomainError


class UserBlockedError(DomainError):
    def __init__(self, username: str) -> None:
        message = f"User {username} is blocked"
        super().__init__(message)


class UserDeleteNotAllowedError(DomainError):
    def __init__(self) -> None:
        message = "Cannot remove super admin"
        super().__init__(message)


class CannotBlockAdminError(DomainError):
    def __init__(self) -> None:
        message = "An admin and super admin cannot be blocked"
        super().__init__(message)


class AdminCannotChangeAdminsRoleError(DomainError):
    def __init__(self) -> None:
        message = "An administrator cannot change the role of another administrator"
        super().__init__(message)


class AdminRegularAssignError(DomainError):
    def __init__(self) -> None:
        message = "A regular administrator cannot assign other administrators"
        super().__init__(message)


class RoleIsUnassignableOrChangable(DomainError):
    def __init__(self) -> None:
        message = "The selected role is unassignable and unchangeable"
        super().__init__(message)


class CannotChangeImageError(DomainError):
    def __init__(self) -> None:
        message = "You cannot change custom images other than your own"
        super().__init__(message)


class UploadImageError(DomainError):
    def __init__(self) -> None:
        message = "Error when uploading image"
        super().__init__(message)


class UserHasNoImageError(DomainError):
    def __init__(self, username: str) -> None:
        message = f"User {username} has no image"
        super().__init__(message)


class ImageReceivingError(DomainError):
    def __init__(self) -> None:
        message = "Error loading image"
        super().__init__(message)


class CannotDeleteImageError(DomainError):
    def __init__(self) -> None:
        message = "You cannot delete custom images other than your own"
        super().__init__(message)
