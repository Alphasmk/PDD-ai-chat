"""Base for domain exceptions"""


class DomainError(Exception):
    """Domain rule violation not tied to domain type construction."""


class DomainTypeError(Exception):
    """Invalid construction of domain types (Value Objects)."""
