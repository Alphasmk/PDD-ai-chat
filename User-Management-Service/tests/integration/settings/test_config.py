"""
Configuration classes
"""

from functools import lru_cache
from tests.integration.settings.separated_configs import (
    DatabaseConfig,
    CacheConfig,
    BrokerConfig,
)


class Config:
    """Main configuration class with all configuration classes"""

    def __init__(self):
        self.cache = CacheConfig()
        self.database = DatabaseConfig()
        self.broker = BrokerConfig()


@lru_cache
def get_test_settings() -> Config:
    return Config()
