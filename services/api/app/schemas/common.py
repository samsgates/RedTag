from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    environment: str
    database: str


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class TimelineItem(BaseModel):
    id: str
    event_type: str
    actor_type: str
    actor_id: str
    payload: dict[str, Any]
    created_at: datetime
