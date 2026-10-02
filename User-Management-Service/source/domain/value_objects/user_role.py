from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"

    @property
    def storage_id(self) -> int:
        return 1 if self is UserRole.USER else 2

    @classmethod
    def from_storage_id(cls, role_id: int) -> "UserRole":
        if role_id == 1:
            return cls.USER
        if role_id == 2:
            return cls.ADMIN
        raise ValueError("Unknown role identifier")
