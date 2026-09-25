from source.application.interfaces import ITokenBlacklist


class FakeRedisTokenBlacklist(ITokenBlacklist):
    def __init__(self):
        self.storage = set()

    async def add(self, user_id: str, refresh_token: str, exp: int = 3600) -> None:
        self.storage.add(refresh_token)

    async def is_blacklisted(self, user_id: str, refresh_token: str) -> bool:
        return refresh_token in self.storage
