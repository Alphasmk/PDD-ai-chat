"""Explicit opt-in URLs for disposable real-service checks."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceConfig:
    postgres_url: str | None
    redis_url: str | None
    broker_url: str | None


def get_test_settings() -> ServiceConfig:
    return ServiceConfig(
        os.getenv("UMS_TEST_POSTGRES_URL"),
        os.getenv("UMS_TEST_REDIS_URL"),
        os.getenv("UMS_TEST_BROKER_URL"),
    )
