from fastapi import FastAPI, Request, Depends
import asyncio
import aiofiles
import logging
import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from utils.ClassLogger import LoggerConfig
from utils.ClassConfig import settings
from utils.Database import engine, get_db, check_db_connection, init_db
from utils.ClassException import ErrorHandler
from utils.ClassSQL import DBQueries

# инициализируем основное логирование
logger_config = LoggerConfig(log_dir=settings.LOG_DIR, log_file='app.log', log_level=settings.LOG_LEVEL, console_output=True, use_json=False)
logger_config.setup_logger()
logger = logger_config.get_logger(__name__)
logger.info("Основной файл main")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
start_time = datetime.datetime.utcnow()

# Инициализация единого обработчика ошибок
error_handler = ErrorHandler(logger)

# Создаём экземпляр для работы с БД и подключаем обработчик ошибок
queries = DBQueries(error_handler).with_handler()


# Глобальная обработка ошибок FastAPI
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Централизованный обработчик всех исключений в приложении"""
    return await error_handler.handle_http_exception(request, exc)


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
        await init_db()     # создаём таблицы после успешного подключения
    asyncio.create_task(lifestile_task(logger=logger, interval=300))    # Запускаем фоновую таску


@app.get("/api/health", tags=["Health"], summary="Роут проверки состояния сервиса")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Проверка состояния сервиса и ключевых зависимостей"""
    status = "healthy"
    try:
        await queries.run_select(db=db, query="SELECT 1", mode="scalar")
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