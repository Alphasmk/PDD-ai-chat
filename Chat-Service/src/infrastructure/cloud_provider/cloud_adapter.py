import base64
from enum import StrEnum

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import (
    GoogleAPIError,
    GoogleModelNotFoundError,
    GoogleRateLimitError
)
from pydantic import BaseModel, Field

from src.settings.config import get_settings
from src.application.interfaces import ICloudProvider

class ImageType(StrEnum):
    ROAD_SCENE = "road_scene"
    TRAFFIC_SIGNS = "traffic_signs"
    EDUCATIONAL = "educational"
    OTHER_TRAFFIC = "other_traffic"
    NOT_TRAFFIC_RELATED = "not_traffic_related"

class TrafficSign(BaseModel):
    name: str = Field(description="Название дорожного знака")
    description: str = Field(
        description="Расположение знака и к какому направлению движения он относится"
    )


class RoadMarking(BaseModel):
    name: str = Field(description="Тип или название дорожной разметки")
    description: str = Field(description="Расположение разметки")


class TrafficLight(BaseModel):
    description: str = Field(
        description=(
            "Расположение светофора, активный сигнал, "
            "стрелки и дополнительные секции"
        )
    )


class Vehicle(BaseModel):
    description: str = Field(
        description=(
            "Тип/цвет транспорта, положение, направление "
            "и предполагаемая траектория"
        )
    )


class TrafficImageAnalysis(BaseModel):
    is_traffic_related: bool = Field(
        description="Связано ли изображение с дорожным движением или ПДД"
    )

    image_type: ImageType = Field(
        description="Фактический тип изображения"
    )

    description: str = Field(
        description=(
            "Подробное описание только непосредственно видимых "
            "на изображении объектов. Ничего не додумывать."
        )
    )

    traffic_signs: list[TrafficSign] = Field(default_factory=list)
    road_markings: list[RoadMarking] = Field(default_factory=list)
    traffic_lights: list[TrafficLight] = Field(default_factory=list)
    vehicles: list[Vehicle] = Field(default_factory=list)

    other_road_elements: list[str] = Field(
        default_factory=list,
        description="Другие значимые элементы дорожной ситуации",
    )

    uncertain_details: list[str] = Field(
        default_factory=list,
        description="Детали, которые невозможно уверенно определить",
    )


class GoogleCloudProvider(ICloudProvider):

    @staticmethod
    async def create_model(model_name: str):
        settings = get_settings()

        return ChatGoogleGenerativeAI(
            model=model_name,
            api_key=settings.gemini.api_key.get_secret_value(),
            temperature=settings.gemini.temperature,
            max_retries=settings.gemini.max_retries,
            # thinking_level=settings.gemini.thinking_level,
        ).with_structured_output(TrafficImageAnalysis)

    async def generate_response(
        self,
        image: bytes,
        mime_type: str,
    ) -> TrafficImageAnalysis:
        settings = get_settings()

        image_base64 = base64.b64encode(image).decode("utf-8")

        messages = [
            SystemMessage(content=settings.gemini.prompt),
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": (
                            "Проанализируй приложенное изображение. "
                            "Описывай исключительно непосредственно "
                            "видимое содержимое. "
                            "Не додумывай отсутствующие объекты."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,"
                                f"{image_base64}"
                            )
                        },
                    },
                ]
            ),
        ]

        last_error: Exception | None = None

        for model_name in settings.gemini.models:
            try:
                model = await self.create_model(model_name)

                return await model.ainvoke(
                    messages,
                    generation_config={
                        "media_resolution": f"MEDIA_RESOLUTION_{settings.gemini.media_resolution.upper()}"
                    },
                )

            except (GoogleModelNotFoundError, GoogleAPIError, GoogleRateLimitError) as exc:
                last_error = exc
                continue

        raise RuntimeError(
            "Ни одна Gemini-модель не доступна"
        ) from last_error
