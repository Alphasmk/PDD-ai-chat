from source.presentation.api.schemas.base import Base
from uuid import UUID
from datetime import datetime
from typing import Optional


class GroupResponse(Base):
    id: UUID
    name: str
    created_at: datetime


class GroupEditData(Base):
    name: Optional[str]


class GroupMessage(Base):
    message: str


class AddUserToGroupRequest(Base):
    user_id: UUID
