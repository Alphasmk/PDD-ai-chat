import pytest
from source.application.dto import UserCreateDTO
from source.application.use_cases import RegisterUser
from source.application.exceptions import (
    EmailTakenError,
    UsernameTakenError,
    PhoneNumberTaken,
)
from source.domain.exceptions import NameLengthError, PasswordLengthError
from tests.adapters.user_repository import FakeUserRepository
from tests.adapters.hasher import FakeHasher


def registration(
    username: str = "alice",
    email: str = "alice@example.com",
    phone: str | None = None,
    name: str = "Alice",
    password: str = "Test1234",
) -> UserCreateDTO:
    return UserCreateDTO(
        name=name,
        surname="Smith",
        username=username,
        email=email,
        password=password,
        phone_number=phone,
    )


async def test_register(repository: FakeUserRepository, hasher: FakeHasher) -> None:
    result = await RegisterUser(repository, hasher).execute(registration())
    stored = repository.users[str(result.id)]
    assert stored.password_hash.value == "hash_Test1234"
    assert not hasattr(result, "image_s3_path")
    assert result.email == "alice@example.com"
    assert result.role.value == "user" and not result.is_blocked


@pytest.mark.parametrize(
    "data,error",
    [
        (registration(name="A"), NameLengthError),
        (registration(password="short"), PasswordLengthError),
    ],
)
async def test_invalid_registration_is_atomic(
    repository: FakeUserRepository,
    hasher: FakeHasher,
    data: UserCreateDTO,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        await RegisterUser(repository, hasher).execute(data)
    assert not repository.users


@pytest.mark.parametrize(
    "data,error",
    [
        (registration("other"), EmailTakenError),
        (registration(email="other@example.com"), UsernameTakenError),
        (registration("other", "other@example.com", "123"), PhoneNumberTaken),
    ],
)
async def test_duplicates(
    repository: FakeUserRepository,
    hasher: FakeHasher,
    data: UserCreateDTO,
    error: type[Exception],
) -> None:
    use_case = RegisterUser(repository, hasher)
    await use_case.execute(registration(phone="123"))
    with pytest.raises(error):
        await use_case.execute(data)
    assert len(repository.users) == 1
