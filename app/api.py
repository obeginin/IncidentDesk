from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from typing import List
from utils.ClassSQL import DBQueries
from utils.ClassError import ErrorHandler
from app import schemas as incident_schemas
from typing import Dict
from app import crud as incident_crud
from utils.ClassConfig import logger_config

logger = logger_config.get_logger(__name__)
error_handler = ErrorHandler(logger)
queries = DBQueries(error_handler)

service = incident_crud.IncidentService(queries, logger=logger)
router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.post("", response_model=incident_schemas.IncidentOut)
async def create_incident(payload: incident_schemas.IncidentCreate, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Запущен ендпоинт: create_incident")
    incident = await service.create_incident(db, payload)
    return incident_schemas.IncidentOut.model_validate(incident)

@router.get("", response_model=List[incident_schemas.IncidentOut])
async def list_incidents(status: str | None = None, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Запущен ендпоинт: list_incidents")
    return await service.list_incidents(db, status)

@router.patch("/{incident_id}/status", response_model=incident_schemas.IncidentOut)
async def update_incident_status(incident_id: int, data: incident_schemas.IncidentUpdateStatus, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Запущен ендпоинт: update_incident_status")
    return await service.update_status(db, incident_id, data.status)

@router.get("/monitoring", response_model=Dict[str, int])
async def monitoring_errors(db: AsyncSession = Depends(get_db)):
    logger.debug(f"Запущен ендпоинт: monitoring_errors")
    return await service.get_error_stats(db)
