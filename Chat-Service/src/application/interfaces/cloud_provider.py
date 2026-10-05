from abc import ABC, abstractmethod
class ICloudProvider(ABC):
    @abstractmethod
    async def create_model(model_name: str): ...

    @abstractmethod
    async def generate_response(
        self,
        image: bytes,
        mime_type: str,
    ): ...