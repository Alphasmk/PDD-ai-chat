from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.test", env_file_encoding="utf-8", extra="ignore"
    )

    @classmethod
    def get_config_with_prefix(cls, prefix: str) -> SettingsConfigDict:
        config = cls.model_config.copy()
        config["env_prefix"] = prefix
        return config
