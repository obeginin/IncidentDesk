from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import Column, Integer, String, DateTime, func
from enum import Enum
from app.database import Base


# Python Enum для статусов и источников
class IncidentStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"

class IncidentSource(str, Enum):
    operator = "operator"
    monitoring = "monitoring"
    partner = "partner"

# Модель инцидента
class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False, default=IncidentStatus.new.value)
    source = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


