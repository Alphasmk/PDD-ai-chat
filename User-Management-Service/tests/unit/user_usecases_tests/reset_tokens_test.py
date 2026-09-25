import pytest
from source.domain.entities.user import UserEntity
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.application.use_cases import ResetTokens
from source.application.exceptions import (
    InvalidTokenError,
    TokenRevokedError,
    UserNotFoundError,
    MissingTokenError,
)


@pytest.mark.asyncio
class TestResetTokens:
    async def test_success(self, repository, token_service, cache_service):
        use_case = ResetTokens(
            repo=repository, token_service=token_service, cache_service=cache_service
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        created_user = await repository.add(existing_user)
        refresh_token_payload = {"sub": str(created_user.id.value), "exp": 3600}
        refresh = await token_service.create_refresh_token(refresh_token_payload)
        new_tokens = await use_case.execute(refresh)
        decoded_access = await token_service.decode_token(new_tokens.access)
        assert decoded_access["sub"] == str(created_user.id.value)
        assert decoded_access["email"] == created_user.email.value
        assert decoded_access["role"] == created_user.role.value

        decoded_refresh = await token_service.decode_token(new_tokens.refresh)
        assert decoded_refresh["sub"] == str(created_user.id.value)

        blacklisted = await cache_service.is_blacklisted(str(created_user.id), refresh)

        assert blacklisted

    @pytest.mark.parametrize(
        "sub, exp", [(None, 3600), (ID(), None)], ids=["none_user_id", "none_exp_token"]
    )
    async def test_invalid_refresh_token(
        self, repository, token_service, cache_service, sub, exp
    ):
        use_case = ResetTokens(
            repo=repository, token_service=token_service, cache_service=cache_service
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        await repository.add(existing_user)
        refresh_token_payload = {"sub": str(sub) if sub else None, "exp": exp}
        refresh = await token_service.create_refresh_token(refresh_token_payload)
        with pytest.raises(InvalidTokenError):
            await use_case.execute(refresh)

    async def test_token_blacklisted(self, repository, token_service, cache_service):
        use_case = ResetTokens(
            repo=repository, token_service=token_service, cache_service=cache_service
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        created_user = await repository.add(existing_user)
        refresh_token_payload = {"sub": str(created_user.id.value), "exp": 3600}
        refresh = await token_service.create_refresh_token(refresh_token_payload)
        await cache_service.add(str(created_user.id), refresh)
        with pytest.raises(TokenRevokedError):
            await use_case.execute(refresh)

    async def test_token_missing(self, repository, token_service, cache_service):
        use_case = ResetTokens(
            repo=repository, token_service=token_service, cache_service=cache_service
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        await repository.add(existing_user)
        with pytest.raises(MissingTokenError):
            await use_case.execute(None)

    async def test_user_from_token_not_exists(
        self, repository, token_service, cache_service
    ):
        use_case = ResetTokens(
            repo=repository, token_service=token_service, cache_service=cache_service
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        await repository.add(existing_user)
        refresh_token_payload = {"sub": str(ID()), "exp": 3600}
        refresh = await token_service.create_refresh_token(refresh_token_payload)
        with pytest.raises(UserNotFoundError):
            await use_case.execute(refresh)
