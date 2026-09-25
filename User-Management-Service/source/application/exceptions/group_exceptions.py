from source.application.exceptions.base import ApplicationException


class CannotCreateGroupError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot create groups"
        super().__init__(message)


class CannotEditGroupError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot edit groups"
        super().__init__(message)


class CannotDeleteGroupError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot delete groups"
        super().__init__(message)


class CannotAddUserToGroupError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot add users to groups"
        super().__init__(message)


class CannotRemoveUserFromGroupError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot remove users from groups"
        super().__init__(message)


class CannotGetGroupUsersError(ApplicationException):
    def __init__(self) -> None:
        message = "You cannot get users in this group"
        super().__init__(message)


class GroupNotFoundError(ApplicationException):
    def __init__(self) -> None:
        message = "Group not found"
        super().__init__(message)


class GroupAlreadyExistsError(ApplicationException):
    def __init__(self, name: str) -> None:
        message = f"Group with name '{name}' already exists"
        super().__init__(message)
