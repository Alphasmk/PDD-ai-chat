from collections.abc import Iterator
import os
from pathlib import Path

import pytest

from source.settings.config import Config, get_settings


@pytest.fixture
def isolated_settings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[None]:
    monkeypatch.chdir(tmp_path)
    for key in os.environ:
        if key.startswith("AWS_"):
            monkeypatch.delenv(key)
    values = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5434",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "disposable",
        "POSTGRES_NAME": "ums_test",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6380",
        "REDIS_PASSWORD": "disposable",
        "BROKER_HOST": "localhost",
        "BROKER_PORT": "5673",
        "BROKER_USER": "test",
        "BROKER_PASSWORD": "disposable",
        "SECRET_KEY": "isolated-config-secret-32-characters",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "%(message)s",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("aws_value", [None, "", "obsolete"])
def test_config_without_image_storage(
    isolated_settings: None, tmp_path: Path, aws_value: str | None
) -> None:
    if aws_value is not None:
        keys = (
            "AWS_ACCESS_KEY_ID",
            "AWS_ACCESS_KEY",
            "AWS_REGION_NAME",
            "AWS_BUCKET_NAME",
        )
        (tmp_path / ".env").write_text(
            "\n".join(f"{key}={aws_value}" for key in keys), encoding="utf-8"
        )
    settings = Config()
    assert not hasattr(settings, "storage")
    assert settings.database.name == "ums_test"
    assert settings.broker.user == "test"
    assert settings.auth.algorithm == "HS256"
    assert get_settings() is get_settings()
    assert not hasattr(get_settings(), "storage")
