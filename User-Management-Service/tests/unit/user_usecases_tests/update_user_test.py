from dataclasses import replace
import pytest
from source.application.dto import UpdateUserDTO
from source.application.use_cases import UpdateUser
from source.application.exceptions import UserNotFoundError
from source.domain.exceptions import NamePatternError, EmailPatternError
from source.domain.value_objects import Name, Email
from tests.adapters.user_repository import FakeUserRepository
from tests.unit.utils.shared_data import make_user, subject


async def test_subject_only_update_and_empty_patch(
    repository: FakeUserRepository,
) -> None:
    alice, bob = (
        await repository.add(make_user()),
        await repository.add(make_user("bob")),
    )
    use_case = UpdateUser(repository)
    assert (await use_case.execute(subject(alice), UpdateUserDTO())).name == "Alice"
    edited = await use_case.execute(
        subject(alice), UpdateUserDTO(name="Jane", email="jane@example.com")
    )
    assert edited.name == "Jane" and edited.email == "jane@example.com"
    assert repository.users[str(bob.id.value)] == bob


@pytest.mark.parametrize(
    "data,error",
    [
        (UpdateUserDTO(name="bad name"), NamePatternError),
        (UpdateUserDTO(email="invalid"), EmailPatternError),
    ],
)
async def test_update_validates_trusted_restoration(
    repository: FakeUserRepository, data: UpdateUserDTO, error: type[Exception]
) -> None:
    user = replace(
        make_user(),
        name=Name.from_trusted("stored invalid"),
        email=Email.from_trusted("stored"),
    )
    await repository.add(user)
    with pytest.raises(error):
        await UpdateUser(repository).execute(subject(user), data)
    assert repository.users[str(user.id.value)] == user


async def test_missing_user(repository: FakeUserRepository) -> None:
    with pytest.raises(UserNotFoundError):
        await UpdateUser(repository).execute(subject(make_user()), UpdateUserDTO())
