import jwt
from datetime import datetime, timedelta, timezone
from source.application.interfaces import ITokenProvider
from source.application.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
)


class TokenProvider(ITokenProvider):
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_expire_minutes: int,
        refresh_expire_days: int,
    ):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_expire_minutes = access_expire_minutes
        self._refresh_expire_days = refresh_expire_days

    async def create_access_token(self, payload: dict) -> str:
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self._access_expire_minutes
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    async def create_refresh_token(self, payload: dict) -> str:
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self._refresh_expire_days)
        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    async def decode_token(self, token: str) -> dict:
        try:
            decoded = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return decoded
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError() from e
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError() from e
