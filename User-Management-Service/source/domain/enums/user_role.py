"""User role class definition"""

from enum import StrEnum


class UserRole(StrEnum):
    """User role class"""

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

    @property
    def is_assignable(self) -> bool:
        """Property to prevent super admin assign"""
        return self != UserRole.SUPER_ADMIN

    @property
    def is_changable(self) -> bool:
        """Property to prevent super admin change"""
        return self != UserRole.SUPER_ADMIN
