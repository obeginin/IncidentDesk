from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker # create_engine
from sqlalchemy.orm import DeclarativeBase
from utils.ClassConfig import settings
import asyncio

from sqlalchemy import text

import logging
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей"""
    pass

# Создание движка и фабрики сессий
engine = create_async_engine(
    settings.ASYNC_DB_URL,
    echo=(settings.DEBUG is True),          # логирует все SQL-запросы в stdout. (если True)
    pool_size=settings.DB_POOL_SIZE,        # Количество соединений в пуле, которое SQLAlchemy держит открытыми одновременно
    max_overflow=settings.DB_MAX_OVERFLOW,  # Сколько дополнительных соединений можно создать сверх pool_size при пиковых нагрузках
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Время ожидания свободного соединения из пула
    pool_recycle=settings.DB_POOL_RECYCLE,  # Время жизни соединения в секундах, после которого оно будет закрыто и заменено новым.
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


async def init_db():
    """Создание таблиц при старте приложения"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)