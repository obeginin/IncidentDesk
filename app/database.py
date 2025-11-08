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

# --- Создание движка ---
engine: AsyncEngine = create_async_engine(
    settings.ASYNC_DB_URL,
    echo=settings.DEBUG,                  # логирует SQL-запросы, если DEBUG = True
    pool_size=settings.DB_POOL_SIZE,      # размер пула соединений
    pool_pre_ping=True,                   # проверка соединений перед использованием
    future=True,                          # API SQLAlchemy 2.0
)


# --- Фабрика сессий ---
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # не очищает объекты после commit
    autocommit=False,
    autoflush=False,
    future=True,
)


async def get_db() -> AsyncSession:
    """Асинхронная зависимость для получения сессии БД"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            logger.exception("Database session error")
            raise
        finally:
            await session.close()


async def check_db_connection(
    engine: AsyncEngine,
    name: str = "default",
    retries: int = 5,
    delay: int = 3,
) -> None:
    """Проверка подключения к базе данных с повторными попытками"""
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info(f"✅ Подключение к базе данных '{name}' установлено.")
            return
        except Exception as e:
            logger.warning(
                f"⚠️ Ошибка подключения к базе '{name}' "
                f"(попытка {attempt}/{retries}): {e}"
            )
            if attempt < retries:
                await asyncio.sleep(delay * attempt)
            else:
                logger.critical(
                    f"❌ Не удалось подключиться к базе '{name}' "
                    f"после {retries} попыток."
                )
                raise



async def run_sql_file(engine: AsyncEngine, sql_file_path: str) -> None:
    """Выполняет SQL-файл при старте приложения"""
    sql_path = Path(sql_file_path)

    if not sql_path.exists():
        raise FileNotFoundError(f"Файл {sql_file_path} не найден")

    sql_content = sql_path.read_text(encoding="utf-8")

    async with engine.begin() as conn:
        await conn.execute(text(sql_content))

    logger.info(f"✅ SQL из {sql_file_path} выполнен успешно")

