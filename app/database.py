from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker # create_engine
from sqlalchemy.orm import DeclarativeBase
from utils.ClassConfig import settings
import asyncio
from sqlalchemy import text
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей"""
    pass

# Создание движка и фабрики сессий
engine = create_async_engine(
    settings.ASYNC_DB_URL,
    echo=(settings.DEBUG is True),          # логирует все SQL-запросы в stdout. (если True)
    pool_size=settings.DB_POOL_SIZE,        # Количество соединений в пуле, которое SQLAlchemy держит открытыми одновременно
    pool_pre_ping=True,                     # проверка соединения перед использованием
    future=True,                            # новый SQLAlchemy 2.0 API
)

async_session_factory = async_sessionmaker(
    bind=engine,                # привязка к движку
    expire_on_commit=False,     # не «сбрасывает» все объекты после commit.
    class_=AsyncSession,
    autocommit=False,           # явно вызываем commit(), а не автокоммит
    autoflush=False,            # не «сбрасывает» изменения автоматически перед запросами
    future=True                 # Включает новый стиль SQLAlchemy 2.0
)


async def get_db() -> AsyncSession:
    """создание и закрытие сессии"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()  # откатываем изменения при ошибке
            logger.exception("Database session error")  # лог с трассировкой
            raise


async def check_db_connection(engine: AsyncEngine, name: str, retries: int = 5, delay: int = 3) -> None:
    """проверка подключения к базе данных с повторными попытками."""
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info(f"✅ Подключение к базе данных '{name}' установлено.")
            return
        except Exception as e:
            logger.warning(f"⚠️ Ошибка подключения к базе '{name}' (Попытка {attempt}/{retries}): {e}")
            if attempt < retries:
                await asyncio.sleep(delay* attempt)
            else:
                logger.critical(f"❌ Не удалось подключиться к базе '{name}' после {retries} попыток.")
                raise


async def run_sql_file(engine: AsyncEngine, sql_file_path: str):
    """Создание таблиц при старте приложения"""
    sql_path = Path(sql_file_path)
    if not sql_path.exists():
        raise FileNotFoundError(f"Файл {sql_file_path} не найден")

    sql_content = sql_path.read_text()
    async with engine.begin() as conn:
        await conn.execute(text(sql_content))
    logger.info(f"✅ SQL из {sql_file_path} выполнен успешно")

