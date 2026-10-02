from dataclasses import replace
import pytest
from source.application.use_cases.admin_use_cases import BlockUser
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


async def test_block_and_noop_preserve_profile() -> None:
    repo = FakeUserRepository()
    admin = await repo.add(replace(make_user("admin"), role=UserRole.ADMIN))
    owner = await repo.add(
        replace(make_user("owner"), role=UserRole.ADMIN, is_superadmin=True)
    )
    user = await repo.add(make_user())
    usecase = BlockUser(lambda: FakeUnitOfWork(repo))
    assert (await usecase.execute(subject(admin), user.id.value)).is_blocked
    blocked = await repo.get_by_id(user.id)
    assert (
        blocked is not None
        and blocked.email == user.email
        and blocked.role is UserRole.USER
    )
    await usecase.execute(subject(admin), user.id.value)
    assert await repo.get_by_id(user.id) == blocked
    with pytest.raises(InvalidTargetStateError):
        await usecase.execute(subject(owner), admin.id.value)
    with pytest.raises(ProtectedAccountError):
        await usecase.execute(subject(admin), owner.id.value)
    with pytest.raises(UserNotFoundError):
        await usecase.execute(subject(admin), ID().value)


async def test_permissions_and_rollback() -> None:
    repo = FakeUserRepository()
    admin = await repo.add(replace(make_user("admin"), role=UserRole.ADMIN))
    user = await repo.add(make_user())
    with pytest.raises(ForbiddenError):
        await BlockUser(lambda: FakeUnitOfWork(repo)).execute(subject(user), ID().value)
    with pytest.raises(ServiceUnavailableError):
        await BlockUser(lambda: FakeUnitOfWork(repo, fail_commit=True)).execute(
            subject(admin), user.id.value
        )
    assert await repo.get_by_id(user.id) == user
