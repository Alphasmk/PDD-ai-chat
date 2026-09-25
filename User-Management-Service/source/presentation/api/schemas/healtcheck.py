from source.presentation.api.schemas.base import Base
from fastapi import status as stat


class HealthcheckResponse(Base):
    status: int = stat.HTTP_200_OK
