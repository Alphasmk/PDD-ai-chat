import pytest
from source.application.use_cases import ResetTokens
from source.application.exceptions import (
    MissingTokenError,
    UserNotFoundError,
    TokenRevokedError,
    InvalidTokenError,
)
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.token_provider import FakeTokenProvider
from tests.adapters.cache_service import FakeRedisTokenBlacklist
from tests.unit.utils.shared_data import make_user


async def test_rotates_and_rejects_replay(
    repository: FakeUserRepository,
    token_service: FakeTokenProvider,
    cache_service: FakeRedisTokenBlacklist,
) -> None:
    user = await repository.add(make_user())
    old = await token_service.create_refresh_token({"sub": str(user.id.value)})
    use_case = ResetTokens(repository, token_service, cache_service)
    new = await use_case.execute(old)
    assert old != new.refresh
    with pytest.raises(TokenRevokedError):
        await use_case.execute(old)
    next_tokens = await use_case.execute(new.refresh)
    assert next_tokens.refresh != new.refresh


async def test_missing_subject_and_cookie(
    repository: FakeUserRepository,
    token_service: FakeTokenProvider,
    cache_service: FakeRedisTokenBlacklist,
) -> None:
    use_case = ResetTokens(repository, token_service, cache_service)
    with pytest.raises(MissingTokenError):
        await use_case.execute(None)
    user = make_user()
    token = await token_service.create_refresh_token({"sub": str(user.id.value)})
    with pytest.raises(UserNotFoundError):
        await use_case.execute(token)
    access = await token_service.create_access_token(
        {"sub": str(user.id.value), "email": user.email.value}
    )
    with pytest.raises(InvalidTokenError):
        await use_case.execute(access)
