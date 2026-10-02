# pylint: disable=no-member
"""
Configuration classes
"""

from functools import lru_cache
from source.settings.separated_configs import (
    AuthConfig,
    CacheConfig,
    DatabaseConfig,
    LoggingConfig,
    BrokerConfig,
)


class Config:
    """Main configuration class with all configuration classes"""

    def __init__(self) -> None:
        self.auth = AuthConfig()
        self.cache = CacheConfig()
        self.database = DatabaseConfig()
        self.logging = LoggingConfig()
        self.broker = BrokerConfig()


@lru_cache
def get_settings() -> Config:
    return Config()
