import pytest
from source.application.use_cases import LoginUser
from source.application.exceptions import InvalidCredentialsError
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.hasher import FakeHasher
from tests.adapters.token_provider import FakeTokenProvider
from tests.unit.utils.shared_data import make_user


async def test_login(
    repository: FakeUserRepository, hasher: FakeHasher, token_service: FakeTokenProvider
) -> None:
    user = await repository.add(make_user())
    tokens = await LoginUser(repository, hasher, token_service).execute(
        "alice", "Test1234"
    )
    claims = await token_service.decode_token(tokens.access)
    assert set(claims) == {"sub", "email", "exp"}
    assert claims["sub"] == str(user.id.value)


@pytest.mark.parametrize(
    "username,password", [("missing", "Test1234"), ("alice", "wrong")]
)
async def test_bad_credentials(
    repository: FakeUserRepository,
    hasher: FakeHasher,
    token_service: FakeTokenProvider,
    username: str,
    password: str,
) -> None:
    await repository.add(make_user())
    with pytest.raises(InvalidCredentialsError):
        await LoginUser(repository, hasher, token_service).execute(username, password)
