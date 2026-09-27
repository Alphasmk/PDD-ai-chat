from uuid import uuid4
from datetime import datetime, timedelta, timezone
import jwt
from source.application.interfaces import ITokenProvider
from source.application.dto.token_dto import AccessPayload, RefreshPayload
from source.application.exceptions import TokenExpiredError, InvalidTokenError


class TokenProvider(ITokenProvider):
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_expire_minutes: int,
        refresh_expire_days: int,
    ) -> None:
        self._secret_key, self._algorithm = secret_key, algorithm
        self._access_expire_minutes, self._refresh_expire_days = (
            access_expire_minutes,
            refresh_expire_days,
        )

    async def create_access_token(self, payload: AccessPayload) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self._access_expire_minutes
        )
        return jwt.encode(
            {"sub": payload["sub"], "email": payload["email"], "exp": expire},
            self._secret_key,
            algorithm=self._algorithm,
        )

    async def create_refresh_token(self, payload: RefreshPayload) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=self._refresh_expire_days)
        return jwt.encode(
            {"sub": payload["sub"], "exp": expire, "jti": str(uuid4())},
            self._secret_key,
            algorithm=self._algorithm,
        )

    async def decode_token(self, token: str) -> dict[str, str | int]:
        try:
            raw: object = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"require": ["sub", "exp"]},
            )
        except jwt.ExpiredSignatureError as error:
            raise TokenExpiredError() from error
        except jwt.InvalidTokenError as error:
            raise InvalidTokenError() from error
        if not isinstance(raw, dict):
            raise InvalidTokenError()
        result: dict[str, str | int] = {}
        for key, value in raw.items():
            if (
                not isinstance(key, str)
                or isinstance(value, bool)
                or not isinstance(value, (str, int))
            ):
                raise InvalidTokenError()
            result[key] = value
        return result
