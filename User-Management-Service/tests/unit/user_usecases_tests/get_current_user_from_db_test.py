import pytest
from source.domain.entities.user import UserEntity
from source.application.use_cases import GetCurrentUserFromDB
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.application.exceptions import (
    UserNotFoundError,
    InvalidTokenError,
    TokenExpiredError,
)


@pytest.mark.asyncio
class TestGetCurrentUserFromDb:
    async def test_success(self, repository, token_service):
        use_case = GetCurrentUserFromDB(repo=repository, token_service=token_service)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        created_user = await repository.add(existing_user)
        access_payload = {
            "sub": str(created_user.id.value),
            "email": created_user.email.value,
            "role": created_user.role.value,
        }
        access = await token_service.create_access_token(access_payload)
        current_user = await use_case.execute(access)
        assert current_user.id == created_user.id.value
        assert current_user.email == created_user.email.value
        assert current_user.role == created_user.role

    async def test_incorrent_sub_from_token(self, repository, token_service):
        use_case = GetCurrentUserFromDB(repo=repository, token_service=token_service)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        await repository.add(existing_user)
        access_payload = {"test": "test"}
        access = await token_service.create_access_token(access_payload)
        with pytest.raises(UserNotFoundError):
            await use_case.execute(access)

    async def test_user_not_exists_from_token(self, repository, token_service):
        use_case = GetCurrentUserFromDB(repo=repository, token_service=token_service)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        created_user = await repository.add(existing_user)
        access_payload = {
            "sub": str(ID()),
            "email": created_user.email.value,
            "role": created_user.role.value,
        }
        access = await token_service.create_access_token(access_payload)
        with pytest.raises(UserNotFoundError):
            await use_case.execute(access)

    async def test_invalid_token_from_user(self, repository, token_service):
        use_case = GetCurrentUserFromDB(repo=repository, token_service=token_service)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )
        await repository.add(existing_user)
        with pytest.raises(InvalidTokenError):
            await use_case.execute("some_invalid_access")

    async def test_user_token_expired(self, repository, token_service):
        use_case = GetCurrentUserFromDB(repo=repository, token_service=token_service)
        existing_user = UserEntity(
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )

        created_user = await repository.add(existing_user)

        access_payload = {
            "sub": str(created_user.id.value),
            "email": created_user.email.value,
            "role": created_user.role.value,
        }
        access = await token_service.create_access_token(access_payload)

        await token_service.force_expire_token(access)
        with pytest.raises(TokenExpiredError):
            await use_case.execute(access)
