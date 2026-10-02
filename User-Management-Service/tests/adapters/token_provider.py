from source.infrastructure.jwt.token_provider import TokenProvider


class FakeTokenProvider(TokenProvider):
    def __init__(self) -> None:
        super().__init__("test-secret-for-unit-tests-32-characters", "HS256", 15, 7)
