from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging
import datetime

from utils.ClassConfig import settings, logger_config
from app.database import engine, get_db, check_db_connection, run_sql_file
from app.api import router as incidents_router

from utils.ClassError import ErrorHandler
from utils.ClassSQL import DBQueries
from utils.handlers import validation_exception_handler


# --- Настройка логирования ---
logger_config.setup_logger()
logger = logger_config.get_logger(__name__)
logger.info("Запуск приложения")

# --- Инициализация вспомогательных классов ---
error_handler = ErrorHandler(logger)
queries = DBQueries(error_handler)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)
start_time = datetime.datetime.utcnow()

# --- Роуты ---
app.include_router(incidents_router, prefix=settings.API_PREFIX)

# --- Обработчики исключений ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный перехват всех исключений приложения."""
    return await error_handler.handle_http_exception(request, exc)

# Ошибки валидации (Pydantic)
app.add_exception_handler(RequestValidationError, validation_exception_handler)



async def lifestile_task(logger: logging.Logger, interval: int = 300):
    """Периодическая проверка активности сервиса."""
    while True:
        logger.info("Service lifecycle: running OK")
        await asyncio.sleep(interval)



@app.on_event("startup")
async def startup_event():
    """Действия при старте приложения."""
    logger.info("🚀 Инициализация приложения и проверка подключений к БД...")
    await check_db_connection(engine=engine, name=settings.DB_NAME)

    # Только в режиме разработки создаём таблицы
    if settings.ENVIRONMENT.lower() == "development":
        try:
            await run_sql_file(engine, "app/sql/create_table.sql")
            logger.info("Таблицы успешно созданы из SQL файла")
        except Exception as e:
            logger.exception(f"Ошибка при создании таблиц: {e}")

    # Запуск фонового мониторинга
    asyncio.create_task(lifestile_task(logger=logger, interval=300))


@app.get("/api/health", tags=["Health"], summary="Проверка состояния сервиса")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Эндпоинт для проверки доступности сервиса и БД."""
    status = "healthy"
    try:
        await queries.run_select(db=db, query="SELECT 1", mode="scalar")
        logger.info("✅ DB connection OK")
    except Exception as e:
        status = "unhealthy"
        logger.exception("❌ Health check failed")

    uptime = (datetime.datetime.utcnow() - start_time).total_seconds()

    return {
        "status": status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "uptime_seconds": int(uptime)
    }
