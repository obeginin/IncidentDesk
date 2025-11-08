from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from pydantic import computed_field
from pydantic import BaseModel
from app.models import IncidentStatus, IncidentSource
from utils.ClassConfig import settings

# --- Схемы Pydantic ---
class IncidentCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=1024)
    status: IncidentStatus
    source: IncidentSource

    model_config = SettingsConfigDict(
        extra="forbid"
    )

class IncidentUpdateStatus(BaseModel):
    status: IncidentStatus

    model_config = SettingsConfigDict(
        extra="forbid"
    )

class IncidentOut(BaseModel):
    id: int
    description: str
    status: IncidentStatus
    source: IncidentSource
    created_at: datetime

    @computed_field
    @property
    def created_at_local(self) -> datetime:
        """Возвращает время в зоне приложения (например, Europe/Moscow)"""
        return self.created_at.astimezone(ZoneInfo(settings.TIMEZONE))

    model_config = SettingsConfigDict(
        from_attributes=True
    )
