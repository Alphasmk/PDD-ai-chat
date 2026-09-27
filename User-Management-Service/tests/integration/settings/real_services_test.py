from datetime import datetime, timezone
from uuid import uuid4
import json
import pytest
from httpx import AsyncClient
from redis.asyncio import Redis
from source.main import app
from source.infrastructure.cache.redis_adapter import RedisTokenBlacklist
from source.infrastructure.message_broker import BrokerHandler, MessagePublisher
from source.presentation.api.dependencies.adapters import (
    get_cache_service,
    get_message_broker_service,
)
from source.application.use_cases import ResetUserPassword
from tests.integration.settings.test_config import get_test_settings
from tests.integration.conftest import account


async def test_real_refresh_revocation_and_expiry(client: AsyncClient) -> None:
    url = get_test_settings().redis_url
    if url is None:
        pytest.skip("Set UMS_TEST_REDIS_URL for disposable Redis integration")
    redis = Redis.from_url(url, decode_responses=True)
    blacklist = RedisTokenBlacklist(redis)
    app.dependency_overrides[get_cache_service] = lambda: blacklist
    try:
        user = await account(client)
        assert (
            await client.post("/api/v1/auth/refresh-token", headers=user.headers)
        ).status_code == 200
        key = f"blacklist:tokens:{user.id}:{user.refresh}"
        ttl = await redis.ttl(key)
        assert ttl > 0
        assert await blacklist.is_blacklisted(user.id, user.refresh)
        assert (
            await client.post("/api/v1/auth/refresh-token", headers=user.headers)
        ).status_code == 200
        client.cookies.set("refresh_token", user.refresh)
        assert (
            await client.post("/api/v1/auth/refresh-token", headers=user.headers)
        ).status_code == 401
        await blacklist.add(
            user.id, "already-expired", int(datetime.now(timezone.utc).timestamp()) - 1
        )
        assert not await blacklist.is_blacklisted(user.id, "already-expired")
    finally:
        # Only keys owned by this test subject; never flush shared Redis.
        if "user" in locals():
            keys = [
                key
                async for key in redis.scan_iter(match=f"blacklist:tokens:{user.id}:*")
            ]
            if keys:
                await redis.delete(*keys)
        await redis.aclose()


async def test_real_password_reset_publish_and_http(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    url = get_test_settings().broker_url
    if url is None:
        pytest.skip("Set UMS_TEST_BROKER_URL for disposable RabbitMQ integration")
    handler = BrokerHandler(url)
    await handler.connect()
    publisher = MessagePublisher(handler)
    queue_name = "reset_test_" + uuid4().hex
    dlq = queue_name + "_dlq"
    monkeypatch.setattr(
        "source.presentation.api.routes.auth_router.QUEUE_NAME", queue_name
    )
    monkeypatch.setattr(
        "source.presentation.api.routes.auth_router.DEAD_LETTER_QUEUE_NAME", dlq
    )
    app.dependency_overrides[get_message_broker_service] = lambda: publisher
    try:
        await ResetUserPassword(publisher).execute(
            "alice@example.com", "test-link", queue_name, dlq
        )
        async with handler.get_channel_pool().acquire() as channel:
            queue = await channel.get_queue(queue_name)
            message = await queue.get(timeout=5, fail=False)
            assert message is not None
            payload: object = json.loads(message.body)
            assert (
                isinstance(payload, dict) and payload["subject"] == "alice@example.com"
            )
            assert "test-link" in str(payload["body"])
            await message.ack()
        response = await client.post(
            "/api/v1/auth/reset-password", json={"email": "bob@example.com"}
        )
        assert response.status_code == 200
        async with handler.get_channel_pool().acquire() as channel:
            queue = await channel.get_queue(queue_name)
            message = await queue.get(timeout=5, fail=False)
            assert message is not None
            payload = json.loads(message.body)
            assert isinstance(payload, dict) and payload["subject"] == "bob@example.com"
            await message.ack()
    finally:
        async with handler.get_channel_pool().acquire() as channel:
            for name in (queue_name, dlq):
                await channel.queue_delete(name)
        await handler.close()
