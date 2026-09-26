from pydantic import BaseModel, ConfigDict


class Base(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)


class ErrorResponse(Base):
    error: str
