from dataclasses import replace
import pytest
from source.application.use_cases.admin_use_cases import ListUsers
from source.application.exceptions.user_exceptions import (
    ForbiddenError,
    UserBlockedError,
)
from source.domain.value_objects.user_role import UserRole
from tests.adapters.user_repository import FakeUserRepository
from tests.unit.utils.shared_data import make_user, subject


async def test_safe_list_and_permissions() -> None:
    repo = FakeUserRepository()
    user = await repo.add(make_user())
    with pytest.raises(ForbiddenError):
        await ListUsers(repo).execute(subject(user), 50, 0)
    admin = await repo.add(replace(make_user("admin"), role=UserRole.ADMIN))
    page = await ListUsers(repo).execute(subject(admin), 50, 0)
    assert len(page.items) == 2
    assert not hasattr(page.items[0], "password_hash") and not hasattr(
        page.items[0], "phone_number"
    )
    assert (await ListUsers(repo).execute(subject(admin), 50, 100)).items == []
    await repo.set_blocked(user.block())
    with pytest.raises(UserBlockedError):
        await ListUsers(repo).execute(subject(user), 50, 0)
