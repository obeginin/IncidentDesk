from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from utils.ClassSQL import DBQueries
from app.schemas import IncidentCreate, IncidentUpdateStatus
from app.models import Incident
from utils.ClassException import AppException
import logging



class IncidentService:
    """CRUD-сервис для работы с инцидентами"""

    def __init__(self, queries: DBQueries, logger):
        self.queries = queries
        self.logger = logging.getLogger(f"{logger.name}.crud")

    # Создание инцидента
    async def create_incident(self, db: AsyncSession, payload: IncidentCreate) -> dict:
        try:
            self.logger.info(f"Запуск функции create_incident с параметрами: {payload}")
            query = """
            INSERT INTO incidents (description, status, source)
            VALUES (:description, :status, :source)
            RETURNING id, description, status, source, created_at
            """
            # Возвращаем словарь нового инцидента
            incident_data = await self.queries.run_insert(
                db,
                query,
                params=payload.model_dump(),
                commit=True,
                return_id=False
            )

            # Получаем полные данные
            incident = await self.queries.run_select(
                db,
                "SELECT * FROM incidents WHERE id = :id",
                params={"id": incident_data},
                mode="mappings_first",
                required=True
            )
            return incident
        except Exception as e:
            # Обработка ошибки через глобальный error_handler
            await self.queries.error_handler.handle_client_error(e, context="perform_task")
            raise

    # Список инцидентов (опционально по статусу)
    async def list_incidents(self, db: AsyncSession, status_filter: str | None = None) -> List[dict]:
        try:
            self.logger.info(f"Запуск функции list_incidents с параметрами: {status_filter}")
            query = "SELECT * FROM incidents"
            params = {}
            if status_filter:
                query += " WHERE status = :status"
                params["status"] = status_filter

            incidents = await self.queries.run_select(
                db,
                query,
                params=params,
                mode="mappings_all"
            )
            return incidents
        except Exception as e:
            # Обработка ошибки через глобальный error_handler
            await self.queries.error_handler.handle_client_error(e, context="list_incidents")
            raise

    # ---------------------------
    # Обновление статуса
    # ---------------------------
    async def update_status(
        self, db: AsyncSession, incident_id: int, payload: IncidentUpdateStatus
    ) -> dict:
        # Проверка существования
        incident = await self.queries.run_select(
            db,
            "SELECT * FROM incidents WHERE id = :id",
            params={"id": incident_id},
            mode="mappings_first"
        )
        if not incident:
            raise AppException(f"Incident with id {incident_id} not found", status_code=404)

        # Обновление
        await self.queries.run_update(
            db,
            "UPDATE incidents SET status = :status WHERE id = :id",
            params={"status": payload.status, "id": incident_id},
            commit=True
        )

        # Возврат обновлённого объекта
        incident = await self.queries.run_select(
            db,
            "SELECT * FROM incidents WHERE id = :id",
            params={"id": incident_id},
            mode="mappings_first",
            required=True
        )
        return incident
