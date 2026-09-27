from dataclasses import replace
import pytest
from source.application.use_cases.bootstrap_use_case import (
    BootstrapSuperadmin,
    BootstrapData,
    InitializationError,
)
from source.domain.value_objects.user_role import UserRole
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.hasher import FakeHasher
from tests.unit.utils.shared_data import make_user


def initial() -> BootstrapData:
    return BootstrapData(
        username="owner",
        email="owner@example.com",
        password="Test1234",
        name="Alice",
        surname="Smith",
    )


async def test_initial_and_existing_creation() -> None:
    repo = FakeUserRepository()
    usecase = BootstrapSuperadmin(repo, FakeHasher())
    assert await usecase.execute(initial) is True
    owner = await repo.get_superadmin()
    assert owner is not None and not owner.is_blocked
    assert owner.password_hash.value == "hash_Test1234"
    assert len(repo.users) == 1

    def missing_settings() -> BootstrapData:
        raise AssertionError(
            "Existing bootstrap must not read or validate initial settings"
        )

    for _ in range(3):
        assert await usecase.execute(missing_settings) is False
        assert await repo.get_superadmin() == owner
    assert await usecase.execute(lambda: replace(initial(), password="bad")) is False


async def test_conflict_does_not_promote() -> None:
    repo = FakeUserRepository()
    user = await repo.add(make_user("owner"))
    with pytest.raises(InitializationError, match="identity_conflict"):
        await BootstrapSuperadmin(repo, FakeHasher()).execute(initial)
    assert repo.users == {str(user.id.value): user}
    assert user.role is UserRole.USER


async def test_invalid_password_without_secret() -> None:
    repo = FakeUserRepository()
    with pytest.raises(InitializationError) as caught:
        await BootstrapSuperadmin(repo, FakeHasher()).execute(
            lambda: replace(initial(), password="secret")
        )
    assert str(caught.value) == "invalid_initial_data"
    assert not repo.users


def test_config_diagnostics_and_lazy_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    from source.settings.separated_configs.bootstrap_config import load_bootstrap_data

    for name in ("USERNAME", "EMAIL", "PASSWORD", "NAME", "SURNAME"):
        monkeypatch.setenv(f"SUPERADMIN_{name}", "")
    with pytest.raises(InitializationError, match="missing_initial_data"):
        load_bootstrap_data()
