from aiohttp import request
from fastapi import FastAPI
import asyncio
import aiofiles
import logging
import datetime

from utils.ClassLogger import LoggerConfig
from utils.ClassConfig import settings
from utils.Database import engine, get_db, check_db_connection, init_db



# инициализируем основное логирование
logger_config = LoggerConfig(log_dir=settings.LOG_DIR, log_file='app.log', log_level=settings.LOG_LEVEL, console_output=True, use_json=False)
logger_config.setup_logger()
logger = logger_config.get_logger(__name__)
logger.info("Основной файл main")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
start_time = datetime.datetime.utcnow()

async def lifestile_task(logger: logging.Logger, interval: int = 300):
    '''Проверка жизни программы'''
    while True:
        logger.info("Service lifestile: running OK")
        await asyncio.sleep(interval)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Проверка подключений к базам данных...")
    await check_db_connection(engine=engine, name=settings.DB_NAME)
    await init_db()  # создаём таблицы после успешного подключения
    asyncio.create_task(lifestile_task(logger=logger, interval=300))    # Запускаем фоновую таску


@app.get("/api/health", tags=["Health"], summary="Роут проверки состояния сервиса")
async def health_check():
    """Проверка состояния сервиса и ключевых зависимостей"""
    status = "healthy"
    # Проверка базы данных
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        status = "unhealthy"

    uptime = (datetime.datetime.utcnow() - start_time).total_seconds()

    return {
        "status": status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "uptime_seconds": int(uptime)
    }