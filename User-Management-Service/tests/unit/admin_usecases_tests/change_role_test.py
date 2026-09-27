from dataclasses import replace
import pytest
from source.application.use_cases.admin_use_cases import ChangeUserRole
from source.application.exceptions import UserNotFoundError
from source.application.exceptions.user_exceptions import (
    ForbiddenError,
    ProtectedAccountError,
    InvalidTargetStateError,
    ServiceUnavailableError,
)
from source.domain.value_objects.user_role import UserRole
from source.domain.value_objects import ID
from tests.adapters.unit_of_work import FakeUnitOfWork
from tests.adapters.user_repository import FakeUserRepository
from tests.unit.utils.shared_data import make_user, subject


async def test_role_changes_noop_and_protected_targets() -> None:
    repo = FakeUserRepository()
    owner = await repo.add(
        replace(make_user("owner"), role=UserRole.ADMIN, is_superadmin=True)
    )
    user = await repo.add(make_user())
    usecase = ChangeUserRole(lambda: FakeUnitOfWork(repo))
    result = await usecase.execute(subject(owner), user.id.value, UserRole.ADMIN)
    admin = await repo.get_by_id(user.id)
    assert result.role is UserRole.ADMIN and admin is not None
    assert admin.id == user.id and admin.email == user.email and admin.name == user.name
    await usecase.execute(subject(owner), user.id.value, UserRole.ADMIN)
    assert await repo.get_by_id(user.id) == admin
    await usecase.execute(subject(owner), user.id.value, UserRole.USER)
    blocked = await repo.get_by_id(user.id)
    assert blocked is not None
    await repo.set_blocked(blocked.block())
    with pytest.raises(InvalidTargetStateError):
        await usecase.execute(subject(owner), user.id.value, UserRole.ADMIN)
    assert (
        await usecase.execute(subject(owner), user.id.value, UserRole.USER)
    ).is_blocked
    with pytest.raises(ProtectedAccountError):
        await usecase.execute(subject(owner), owner.id.value, UserRole.USER)
    with pytest.raises(UserNotFoundError):
        await usecase.execute(subject(owner), ID().value, UserRole.ADMIN)


async def test_permissions_and_commit_failure_do_not_change_data() -> None:
    repo = FakeUserRepository()
    owner = await repo.add(
        replace(make_user("owner"), role=UserRole.ADMIN, is_superadmin=True)
    )
    user = await repo.add(make_user())
    with pytest.raises(ForbiddenError):
        await ChangeUserRole(lambda: FakeUnitOfWork(repo)).execute(
            subject(user), ID().value, UserRole.ADMIN
        )
    with pytest.raises(ServiceUnavailableError):
        await ChangeUserRole(lambda: FakeUnitOfWork(repo, fail_commit=True)).execute(
            subject(owner), user.id.value, UserRole.ADMIN
        )
    assert await repo.get_by_id(user.id) == user
