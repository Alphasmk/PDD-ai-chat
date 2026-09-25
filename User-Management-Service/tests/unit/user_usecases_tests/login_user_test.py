import pytest
from source.application.use_cases import LoginUser
from source.domain.entities.user import UserEntity
from source.domain.value_objects import Email, PasswordHash, Name
from source.domain.exceptions import UserBlockedError
from source.application.exceptions import InvalidCredentialsError


@pytest.mark.asyncio
class TestLoginUser:
    async def test_success(self, repository, hasher, token_service):
        use_case = LoginUser(
            repo=repository, hasher=hasher, token_service=token_service
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )

        created_user = await repository.add(existing_user)

        entered_password = "test1234"
        tokens = await use_case.execute(created_user.username, entered_password)
        assert tokens is not None

        expected_access_payload = {
            "sub": str(created_user.id.value),
            "email": created_user.email.value,
            "role": created_user.role.value,
            "group_id": "",
        }
        expected_access = await token_service.create_access_token(
            expected_access_payload
        )
        assert tokens.access == expected_access

        expected_refresh_payload = {"sub": str(created_user.id.value)}
        expected_refresh = await token_service.create_refresh_token(
            expected_refresh_payload
        )
        assert tokens.refresh == expected_refresh

    @pytest.mark.parametrize(
        "entered_username, entered_password",
        [("testusername", "test12345"), ("username", "test1234")],
        ids=["user_entered_invalid_passsword", "user_entered_invalid_username"],
    )
    async def test_login_with_invalid_credentials(
        self, repository, hasher, token_service, entered_username, entered_password
    ):
        use_case = LoginUser(
            repo=repository, hasher=hasher, token_service=token_service
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )

        await repository.add(existing_user)

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(entered_username, entered_password)

    async def test_login_with_blocking(self, repository, hasher, token_service):
        use_case = LoginUser(
            repo=repository, hasher=hasher, token_service=token_service
        )
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )

        created_user = await repository.add(existing_user)

        await repository.change_block_state(created_user.id)

        entered_password = "test1234"
        with pytest.raises(UserBlockedError):
            await use_case.execute(created_user.username, entered_password)
