from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from utils.ClassSQL import DBQueries
from app.schemas import IncidentCreate
from utils.ClassException import AppException
import logging

class IncidentService:
    """CRUD-сервис для работы с инцидентами"""

    def __init__(self, queries: DBQueries, logger: logging.Logger):
        self.queries = queries
        self.logger = logger

    async def create_incident(self, db: AsyncSession, payload: IncidentCreate) -> dict:
        """Создание нового инцидента"""
        try:
            params = payload.model_dump()
            params['status'] = "new"
            self.logger.info(f"Запуск функции create_incident с параметрами: {payload}")

            query = """
            INSERT INTO incidents (description, status, source)
            VALUES (:description, :status, :source)
            RETURNING id
            """
            inserted_id = await self.queries.run_insert(
                db, query, params=params, commit=True, return_id=True
            )

            incident = await self.queries.run_select(
                db,
                "SELECT * FROM incidents WHERE id = :id",
                params={"id": inserted_id},
                mode="mappings_first",
                required=True
            )

            self.logger.info(f"Инцидент создан: {incident}")
            return incident
        except Exception as e:
            await self.queries.error_handler.handle_client_error(e, context="create_incident")
            raise

    async def list_incidents(self, db: AsyncSession, status_filter: str | None = None) -> List[dict]:
        """Получение списка инцидентов (опционально по статусу)"""
        try:
            self.logger.info(f"Запуск функции list_incidents с фильтром: {status_filter}")
            query = "SELECT * FROM incidents"
            params = {}
            if status_filter:
                query += " WHERE status = :status"
                params["status"] = status_filter

            incidents = await self.queries.run_select(
                db, query, params=params, mode="mappings_all"
            )
            return incidents
        except Exception as e:
            await self.queries.error_handler.handle_client_error(e, context="list_incidents")
            raise

    async def update_status(self, db: AsyncSession, incident_id: int, status: str) -> dict:
        """Обновление статуса инцидента"""
        incident = await self.queries.run_select(
            db,
            "SELECT * FROM incidents WHERE id = :id",
            params={"id": incident_id},
            mode="mappings_first"
        )
        if not incident:
            raise AppException(f"Инцидент с id {incident_id} не найден", status_code=404)

        await self.queries.run_update(
            db,
            "UPDATE incidents SET status = :status WHERE id = :id",
            params={"status": status, "id": incident_id},
            commit=True
        )

        incident = await self.queries.run_select(
            db,
            "SELECT * FROM incidents WHERE id = :id",
            params={"id": incident_id},
            mode="mappings_first",
            required=True
        )

        self.logger.info(f"Инцидент обновлён: {incident}")
        return incident
