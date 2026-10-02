from source.domain.entities.user import UserEntity
from source.domain.value_objects.user_role import UserRole
from source.domain.exceptions.user_access_exceptions import Forbidden, UserBlocked


def require_active(user: UserEntity) -> None:
    if user.is_blocked:
        raise UserBlocked()


def require_admin(user: UserEntity) -> None:
    require_active(user)
    if user.role is not UserRole.ADMIN:
        raise Forbidden()


def require_superadmin(user: UserEntity) -> None:
    require_active(user)
    if not user.is_superadmin:
        raise Forbidden()
