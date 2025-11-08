from fastapi import FastAPI, Request, Depends
import asyncio
import logging
import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from utils.ClassConfig import settings
from app.database import engine, get_db, check_db_connection, run_sql_file
from app.api import router as incidents_router
from app.core import logger_config
from utils.ClassException import ErrorHandler
from utils.ClassSQL import DBQueries

from app.models import Incident
logger_config.setup_logger()
logger = logger_config.get_logger(__name__)
logger.info("Запуск приложения")
# создаём обработчики, завязанные на этот логгер
error_handler = ErrorHandler(logger)
queries = DBQueries(error_handler)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
start_time = datetime.datetime.utcnow()


# Глобальная обработка ошибок FastAPI
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Централизованный обработчик всех исключений в приложении"""
    return await error_handler.handle_http_exception(request, exc)

app.include_router(incidents_router, prefix=settings.API_PREFIX)

async def lifestile_task(logger: logging.Logger, interval: int = 300):
    '''Проверка жизни программы'''
    while True:
        logger.info("Service lifestile: running OK")
        await asyncio.sleep(interval)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Проверка подключений к базам данных...")
    await check_db_connection(engine=engine, name=settings.DB_NAME)
    if settings.ENVIRONMENT == "development":
        await run_sql_file(engine, "app/sql/create_table.sql")     # создаём таблицы после успешного подключения
        logger.info("Таблицы успешно созданы из SQL файла")
    asyncio.create_task(lifestile_task(logger=logger, interval=300))    # Запускаем фоновую таску


@app.get("/api/health", tags=["Health"], summary="Роут проверки состояния сервиса")
async def health_check(db: AsyncSession = Depends(get_db)):
    status = "healthy"
    try:
        await queries.run_select(db=db, query="SELECT 1", mode="scalar")
        logger.info("DB connection OK")
    except Exception as e:
        status = "unhealthy"
        logger.exception("Health check failed")  # ← вот здесь будет трассировка

    uptime = (datetime.datetime.utcnow() - start_time).total_seconds()
    return {
        "status": status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "uptime_seconds": int(uptime)
    }