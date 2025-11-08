from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from functools import wraps
from typing import Any, Optional
from utils.ClassError import AppException
from utils.ClassException import ErrorHandler

logger = logging.getLogger(__name__)
error_handler = ErrorHandler(logger)

def db_operation(context: str = "DB", error_handler: Optional[ErrorHandler] = None):
    """
    Асинхронный декоратор для обработки ошибок SQLAlchemy/DB.
    Логирует ошибку через переданный error_handler и выбрасывает AppException.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db: AsyncSession = kwargs.get("db") or (args[0] if args else None)
            try:
                return await func(*args, **kwargs)
            except IntegrityError as e:
                if db:
                    await db.rollback()
                if error_handler:
                    info = await error_handler.handle_client_error(e, context=context)
                    raise AppException(info.message, status_code=400)
                raise
            except SQLAlchemyError as e:
                if db:
                    await db.rollback()
                if error_handler:
                    info = await error_handler.handle_client_error(e, context=context)
                    raise AppException(info.message, status_code=500)
                raise
            except Exception as e:
                if db:
                    await db.rollback()
                if error_handler:
                    info = await error_handler.handle_client_error(e, context=context)
                    raise AppException(info.message, status_code=500)
                raise
        return wrapper
    return decorator


class DBQueries:
    """Класс с методами для безопасной работы с БД"""

    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler

    @db_operation(context="DB_SELECT", error_handler=None)
    async def run_select(
        self,
        db: AsyncSession,
        query: str,
        params: dict | None = None,
        mode: str = "mappings_all",
        required: bool = False,
    ):
        result = await db.execute(text(query), params or {})
        match mode:
            case "scalar": data = result.scalar()
            case "scalars_all": data = result.scalars().all()
            case "mappings_first": data = result.mappings().first()
            case "mappings_all": data = result.mappings().all()
            case "one_or_none": data = result.one_or_none()
            case "first": data = result.first()
            case _: raise AppException(f"Неизвестный режим выборки: {mode}", status_code=400)

        if required and not data:
            raise AppException("Пустой результат запроса", status_code=404)
        return data

    @db_operation(context="DB_UPDATE", error_handler=None)
    async def run_update(self, db: AsyncSession, query: str, params: dict | None = None, commit: bool = True):
        result = await db.execute(text(query), params or {})
        if commit:
            await db.commit()
        return result.rowcount

    @db_operation(context="DB_INSERT", error_handler=None)
    async def run_insert(self, db: AsyncSession, query: str, params: dict | None = None, commit: bool = True, return_id: bool = False):
        result = await db.execute(text(query), params or {})
        if commit:
            await db.commit()
        if return_id:
            inserted_id = result.scalar()
            return inserted_id if inserted_id is not None else 0
        return result.rowcount

    @db_operation(context="DB_DELETE", error_handler=None)
    async def run_delete(self, db: AsyncSession, query: str, params: dict | None = None, commit: bool = True):
        result = await db.execute(text(query), params or {})
        if commit:
            await db.commit()
        return result.rowcount

    def with_handler(self):
        """Возвращает новый экземпляр, где error_handler внедрён в декораторы"""
        for name in dir(self):
            func = getattr(self, name)
            if callable(func) and hasattr(func, "__wrapped__"):  # обёрнут декоратором
                setattr(self, name, db_operation(context=name.upper(), error_handler=self.error_handler)(func.__wrapped__))
        return self
