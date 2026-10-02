import datetime
from redis.asyncio import Redis
from source.application.interfaces import ITokenBlacklist


class RedisTokenBlacklist(ITokenBlacklist):
    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client

    async def add(self, user_id: str, refresh_token: str, exp: int) -> None:
        """Blacklist refresh token method"""
        current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        ttl = exp - current_time
        if ttl > 0:
            await self.redis.set(
                name=f"blacklist:tokens:{user_id}:{refresh_token}",
                value=refresh_token,
                ex=ttl,
            )

    async def is_blacklisted(self, user_id: str, refresh_token: str) -> bool:
        """Check if refresh token is blacklisted method"""
        result: object = await self.redis.exists(
            f"blacklist:tokens:{user_id}:{refresh_token}"
        )
        if not isinstance(result, int):
            raise RuntimeError("Redis returned an invalid blacklist count")
        return result > 0
