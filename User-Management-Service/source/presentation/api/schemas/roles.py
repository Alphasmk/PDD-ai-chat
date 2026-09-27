from source.domain.value_objects.user_role import UserRole
from source.presentation.api.schemas.base import Base


class RoleResponse(Base):
    value: UserRole
    label: str


class RolesResponse(Base):
    items: list[RoleResponse]
