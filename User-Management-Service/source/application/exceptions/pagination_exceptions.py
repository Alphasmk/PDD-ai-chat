from source.application.exceptions.base import ApplicationException


class InvalidSortFieldError(ApplicationException):
    def __init__(self) -> None:
        message = "Cannot sort by this field"
        super().__init__(message)
