import json
import base64
from source.application.interfaces import ITokenProvider
from source.application.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
)


class FakeTokenProvider(ITokenProvider):
    def __init__(self):
        self.expired_tokens = set()

    async def create_access_token(self, payload: dict) -> str:
        json_bytes = json.dumps(payload).encode("utf-8")
        encoded_payload = base64.urlsafe_b64encode(json_bytes).decode("utf-8")

        return f"fake_token_{encoded_payload}"

    async def create_refresh_token(self, payload: dict) -> str:
        json_bytes = json.dumps(payload).encode("utf-8")
        encoded_payload = base64.urlsafe_b64encode(json_bytes).decode("utf-8")

        return f"fake_token_{encoded_payload}"

    async def decode_token(self, token: str) -> dict:
        if not token.startswith("fake_token_"):
            raise InvalidTokenError()

        if token in self.expired_tokens:
            raise TokenExpiredError()

        encoded_payload = token.replace("fake_token_", "")

        try:
            json_bytes = base64.urlsafe_b64decode(encoded_payload)
            return json.loads(json_bytes)
        except Exception as e:
            raise InvalidTokenError() from e

    async def force_expire_token(self, token: str):
        self.expired_tokens.add(token)
