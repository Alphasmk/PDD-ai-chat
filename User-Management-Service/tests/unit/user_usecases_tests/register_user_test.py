import pytest
from source.domain.value_objects import ID
from source.application.use_cases import RegisterUser
from source.application.dto import UserCreateDTO
from source.application.exceptions import (
    EmailTakenError,
    UsernameTakenError,
    PhoneNumberTaken,
)


@pytest.mark.asyncio
class TestRegisterUser:
    async def test_success(self, hasher, repository):
        use_case = RegisterUser(repo=repository, hasher=hasher)
        user = UserCreateDTO(
            name="testname",
            surname="testsurname",
            username="testusername",
            password="test1234",
            email="test@test.com",
        )
        created_user = await use_case.execute(user)

        assert created_user is not None
        saved_user = await repository.get_by_id(ID(created_user.id))
        assert saved_user is not None

        assert saved_user.password_hash.value == "hash_test1234"
        assert saved_user.id.value == created_user.id

    async def test_user_with_email_already_exists(self, hasher, repository):
        use_case = RegisterUser(repo=repository, hasher=hasher)
        user = UserCreateDTO(
            name="testname",
            surname="testsurname",
            username="testusername",
            password="test1234",
            email="test@test.com",
        )
        await use_case.execute(user)
        bad_user = UserCreateDTO(
            name="test",
            surname="test",
            username="test",
            password="test1234",
            email="test@test.com",
        )
        with pytest.raises(EmailTakenError):
            await use_case.execute(bad_user)

    async def test_user_with_username_already_exists(self, hasher, repository):
        use_case = RegisterUser(repo=repository, hasher=hasher)
        user = UserCreateDTO(
            name="testname",
            surname="testsurname",
            username="testusername",
            password="test1234",
            email="test@test.com",
        )
        await use_case.execute(user)
        bad_user = UserCreateDTO(
            name="test",
            surname="test",
            username="testusername",
            password="test1234",
            email="testemail@test.com",
        )
        with pytest.raises(UsernameTakenError):
            await use_case.execute(bad_user)

    async def test_user_with_phone_number_already_exists(self, hasher, repository):
        use_case = RegisterUser(repo=repository, hasher=hasher)
        user = UserCreateDTO(
            name="testname",
            surname="testsurname",
            username="testusername",
            password="test1234",
            email="test@test.com",
            phone_number="some_number",
        )
        await use_case.execute(user)
        bad_user = UserCreateDTO(
            name="test",
            surname="test",
            username="test",
            password="test1234",
            email="testemail@test.com",
            phone_number="some_number",
        )
        with pytest.raises(PhoneNumberTaken):
            await use_case.execute(bad_user)
