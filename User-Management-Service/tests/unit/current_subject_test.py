import pytest
from source.application.use_cases import GetCurrentUserFromToken
from source.application.exceptions import (
    UserNotFoundError,
    InvalidTokenError,
    TokenExpiredError,
)
from tests.adapters.user_repository import FakeUserRepository
from source.infrastructure.jwt import TokenProvider
from tests.unit.utils.shared_data import make_user


async def test_existing_and_deleted_subject() -> None:
    repository = FakeUserRepository()
    user = await repository.add(make_user())
    provider = TokenProvider(
        "subject-test-secret-at-least-32-characters", "HS256", 15, 7
    )
    token = await provider.create_access_token(
        {"sub": str(user.id.value), "email": user.email.value}
    )
    use_case = GetCurrentUserFromToken(repository, provider)
    assert (await use_case.execute(token)).user_id == user.id.value
    await repository.delete(user)
    with pytest.raises(UserNotFoundError):
        await use_case.execute(token)


async def test_invalid_uuid_refresh_as_access_and_expiry() -> None:
    repository = FakeUserRepository()
    provider = TokenProvider(
        "subject-test-secret-at-least-32-characters", "HS256", 15, 7
    )
    use_case = GetCurrentUserFromToken(repository, provider)
    token = await provider.create_access_token(
        {"sub": "not-uuid", "email": "alice@example.com"}
    )
    with pytest.raises(InvalidTokenError):
        await use_case.execute(token)
    user = await repository.add(make_user())
    token = await provider.create_refresh_token({"sub": str(user.id.value)})
    with pytest.raises(InvalidTokenError):
        await use_case.execute(token)
    expired = TokenProvider(
        "subject-test-secret-at-least-32-characters", "HS256", -1, 7
    )
    token = await expired.create_access_token(
        {"sub": str(user.id.value), "email": user.email.value}
    )
    with pytest.raises(TokenExpiredError):
        await use_case.execute(token)
