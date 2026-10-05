# pylint: disable=no-member
"""
Configuration classes
"""

from functools import lru_cache
from src.settings.separated_configs import (
    AuthConfig,
    GeminiConfig
)


class Config:
    """Main configuration class with all configuration classes"""

    def __init__(self):
        self.auth = AuthConfig()
        self.gemini = GeminiConfig()


@lru_cache
def get_settings() -> Config:
    return Config()