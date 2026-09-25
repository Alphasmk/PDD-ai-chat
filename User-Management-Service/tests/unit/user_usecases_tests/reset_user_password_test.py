import pytest
from source.application.use_cases import ResetUserPassword
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.entities.user import UserEntity


@pytest.mark.asyncio
class TestResetUserPassword:
    async def test_success(self, message_publisher, repository):
        use_case = ResetUserPassword(broker_service=message_publisher)
        existing_user = UserEntity(
            id=ID(),
            name=Name("testname"),
            surname=Name("testsurname"),
            username="testusername",
            password_hash=PasswordHash("hash_test1234"),
            email=Email("test@test.com"),
        )

        created_user = await repository.add(existing_user)

        await use_case.execute(created_user.email.value, "Test message", "Test", "Test")

        assert created_user.email.value in [
            message["subject"] for message in await message_publisher.get_messages()
        ]
