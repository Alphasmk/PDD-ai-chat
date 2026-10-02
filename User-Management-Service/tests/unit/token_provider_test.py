from datetime import datetime, timezone
from unittest.mock import patch
import jwt
import pytest
from source.infrastructure.jwt import TokenProvider
from source.application.exceptions import InvalidTokenError, TokenExpiredError


async def test_exact_claims_unique_same_second() -> None:
    provider = TokenProvider("unit-test-secret-at-least-32-characters", "HS256", 15, 7)
    with patch("source.infrastructure.jwt.token_provider.datetime") as clock:
        clock.now.return_value = datetime.now(timezone.utc)
        access = await provider.create_access_token(
            {"sub": "subject", "email": "alice@example.com"}
        )
        first = await provider.create_refresh_token({"sub": "subject"})
        second = await provider.create_refresh_token({"sub": "subject"})
    assert set(await provider.decode_token(access)) == {"sub", "email", "exp"}
    claims = await provider.decode_token(first)
    assert set(claims) == {"sub", "exp", "jti"}
    assert first != second
    assert claims["jti"] != (await provider.decode_token(second))["jti"]


async def test_invalid_expired_tokens() -> None:
    provider = TokenProvider("unit-test-secret-at-least-32-characters", "HS256", -1, -1)
    with pytest.raises(InvalidTokenError):
        await provider.decode_token("invalid")
    expired = await provider.create_access_token(
        {"sub": "subject", "email": "alice@example.com"}
    )
    with pytest.raises(TokenExpiredError):
        await provider.decode_token(expired)
    missing_exp = jwt.encode(
        {"sub": "subject"}, "unit-test-secret-at-least-32-characters", algorithm="HS256"
    )
    with pytest.raises(InvalidTokenError):
        await provider.decode_token(missing_exp)
