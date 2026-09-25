from source.settings.separated_configs.base import ConfigBase
from pydantic_settings import SettingsConfigDict


class LoggingConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
