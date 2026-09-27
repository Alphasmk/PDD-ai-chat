from source.domain.exceptions.base import DomainError


class Forbidden(DomainError):
    pass


class UserBlocked(DomainError):
    pass


class ProtectedAccount(DomainError):
    pass


class InvalidTargetState(DomainError):
    pass
