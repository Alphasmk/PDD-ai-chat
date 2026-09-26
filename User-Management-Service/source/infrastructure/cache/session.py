from collections.abc import AsyncIterator
from functools import lru_cache
from redis.asyncio import Redis
from source.infrastructure.interfaces import ICacheSessionmaker


class CacheSessionmaker(ICacheSessionmaker):
    def __init__(self) -> None:
        self._client: Redis | None = None

    async def init_db(self, db_url: str) -> None:
        self._client = Redis.from_url(db_url, decode_responses=True)

    async def get_session(self) -> AsyncIterator[Redis]:
        if self._client is None:
            raise RuntimeError("Cache not initialized")
        yield self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


@lru_cache
def get_cache_database() -> CacheSessionmaker:
    return CacheSessionmaker()
