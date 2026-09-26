import pytest
from source.application.use_cases import GetCurrentUserFromDB
from source.application.exceptions import UserNotFoundError
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.token_provider import FakeTokenProvider
from tests.unit.utils.shared_data import make_user


async def test_reads_existing_subject(
    repository: FakeUserRepository, token_service: FakeTokenProvider
) -> None:
    user = await repository.add(make_user(image_s3_path="own-key"))
    await repository.add(make_user("bob"))
    token = await token_service.create_access_token(
        {"sub": str(user.id.value), "email": user.email.value}
    )
    result = await GetCurrentUserFromDB(repository, token_service).execute(token)
    assert result.id == user.id.value and result.image_s3_path == "own-key"
    await repository.delete(user)
    with pytest.raises(UserNotFoundError):
        await GetCurrentUserFromDB(repository, token_service).execute(token)
