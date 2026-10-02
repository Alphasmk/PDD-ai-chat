from dataclasses import FrozenInstanceError, replace
import pytest
from source.domain.value_objects.user_role import UserRole
from source.domain.exceptions.user_access_exceptions import (
    InvalidTargetState,
    ProtectedAccount,
)
from tests.unit.utils.shared_data import make_user


def test_roles_and_defaults() -> None:
    user = make_user()
    assert set(UserRole) == {UserRole.USER, UserRole.ADMIN}
    assert user.role is UserRole.USER and not user.is_blocked
    with pytest.raises(FrozenInstanceError):
        setattr(user, "is_blocked", True)


def test_transitions_preserve_profile_and_noop_timestamp() -> None:
    user = make_user()
    assert user.change_role(UserRole.USER) is user
    admin = user.change_role(UserRole.ADMIN)
    assert admin.id == user.id and admin.email == user.email
    assert admin.updated_at is not None
    assert admin.change_role(UserRole.ADMIN) is admin
    blocked = admin.change_role(UserRole.USER).block()
    assert blocked.block() is blocked
    assert blocked.change_role(UserRole.USER) is blocked
    with pytest.raises(InvalidTargetState):
        blocked.change_role(UserRole.ADMIN)


def test_protected_transitions() -> None:
    user = make_user()
    admin = user.change_role(UserRole.ADMIN)
    superadmin = replace(user, role=UserRole.ADMIN, is_superadmin=True)
    with pytest.raises(InvalidTargetState):
        admin.block()
    for role in UserRole:
        with pytest.raises(ProtectedAccount):
            superadmin.change_role(role)
    with pytest.raises(ProtectedAccount):
        superadmin.block()
    with pytest.raises(ProtectedAccount):
        superadmin.ensure_deletable()
    with pytest.raises(InvalidTargetState):
        replace(admin, is_blocked=True)
    with pytest.raises(InvalidTargetState):
        replace(user, is_superadmin=True)
