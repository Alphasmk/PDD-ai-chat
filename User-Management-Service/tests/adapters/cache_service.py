from source.application.interfaces import ITokenBlacklist


class FakeRedisTokenBlacklist(ITokenBlacklist):
    def __init__(self) -> None:
        self.storage: set[tuple[str, str]] = set()

    async def add(self, user_id: str, refresh_token: str, exp: int) -> None:
        self.storage.add((user_id, refresh_token))

    async def is_blacklisted(self, user_id: str, refresh_token: str) -> bool:
        return (user_id, refresh_token) in self.storage
