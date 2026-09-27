from dataclasses import replace
from uuid import UUID
import pytest
from source.domain.value_objects import ID, Name, Email, RawPassword, PasswordHash
from source.domain.exceptions import (
    NameLengthError,
    NamePatternError,
    EmailPatternError,
    PasswordLengthError,
    PasswordPatternError,
)
from tests.unit.utils.shared_data import make_user


@pytest.mark.parametrize("value", ["Al", "O'Neil", "Иван", "Jean-Luc", "A" * 20])
def test_valid_names(value: str) -> None:
    assert Name(value).value == value


@pytest.mark.parametrize(
    "value,error",
    [
        ("", NameLengthError),
        ("A", NameLengthError),
        ("A" * 21, NameLengthError),
        ("Ab2", NamePatternError),
        ("A B", NamePatternError),
    ],
)
def test_invalid_names(value: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        Name(value)


def test_email_and_trusted_restore() -> None:
    assert Email("alice@example.com").value == "alice@example.com"
    with pytest.raises(EmailPatternError):
        Email("invalid")
    restored = replace(
        make_user(),
        name=Name.from_trusted("stored value"),
        email=Email.from_trusted("stored"),
    )
    assert restored.name.value == "stored value"
    with pytest.raises(NamePatternError):
        Name("new invalid")
    with pytest.raises(EmailPatternError):
        Email("new invalid")


@pytest.mark.parametrize("value", ["Test1234", "A" * 20, "Abcd@#+="])
def test_valid_password(value: str) -> None:
    assert RawPassword(value).value == value
    assert value not in repr(RawPassword(value))


@pytest.mark.parametrize(
    "value,error",
    [
        ("abc", PasswordLengthError),
        ("A" * 21, PasswordLengthError),
        ("Abcd123!", PasswordPatternError),
        ("Abcd 123", PasswordPatternError),
    ],
)
def test_invalid_password(value: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        RawPassword(value)


def test_id_and_password_hash() -> None:
    first, second = ID(), ID()
    assert isinstance(first.value, UUID) and first != second
    assert ID(first.value) == first
    assert PasswordHash("opaque").value == "opaque"
    assert "opaque" not in repr(PasswordHash("opaque"))
