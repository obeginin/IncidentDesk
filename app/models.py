from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, func
from enum import Enum
from app.database import Base

class IncidentStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"

class IncidentSource(str, Enum):
    operator = "operator"
    monitoring = "monitoring"
    partner = "partner"

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    status = Column(SAEnum(IncidentStatus, name="incident_status"), nullable=False, server_default=IncidentStatus.new.value)
    source = Column(SAEnum(IncidentSource, name="incident_source"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
