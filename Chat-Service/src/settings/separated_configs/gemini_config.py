from pathlib import Path
from typing import Literal

from src.settings.separated_configs.base import ConfigBase
from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict


class GeminiConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="GEMINI_")

    models: list[str]
    api_key: SecretStr
    temperature: float
    max_retries: int
    thinking_level: Literal["low", "medium", "high"] = "low"
    media_resolution: Literal["low", "medium", "high"] = "medium"

    prompt_file: Path = Path(__file__).with_name("gemini_prompt.txt")

    @property
    def prompt(self) -> str:
        return self.prompt_file.read_text(encoding="utf-8").strip()
