from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from functools import wraps
from utils.ClassError import AppException, ErrorHandler


logger = logging.getLogger(__name__)


def db_operation(context: str = "DB"):
    """
    Декоратор для безопасной работы с БД.
    Ожидает, что функция принимает аргумент db: AsyncSession.
    Автоматически выполняет rollback при ошибках и логирует через ErrorHandler (если задан).
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            db: AsyncSession | None = kwargs.get("db")
            handler: ErrorHandler | None = getattr(self, "error_handler", None)

            try:
                return await func(self, *args, **kwargs)

            except IntegrityError as e:
                if db:
                    try:
                        await db.rollback()
                    except Exception as rb_err:
                        logger.warning(f"Ошибка при rollback после IntegrityError: {rb_err}")
                if handler:
                    await handler.handle_client_error(e, context=context)
                raise AppException(
                    "Ошибка работы с базой данных (конфликт данных)",
                    status_code=400,
                    original_exc=e,
                ) from e

            except SQLAlchemyError as e:
                if db:
                    try:
                        await db.rollback()
                    except Exception as rb_err:
                        logger.warning(f"Ошибка при rollback после SQLAlchemyError: {rb_err}")
                if handler:
                    await handler.handle_client_error(e, context=context)
                raise AppException(
                    "Ошибка работы с базой данных",
                    status_code=500,
                    original_exc=e,
                ) from e

            except Exception as e:
                if db:
                    try:
                        await db.rollback()
                    except Exception as rb_err:
                        logger.warning(f"Ошибка при rollback после Exception: {rb_err}")
                if handler:
                    await handler.handle_client_error(e, context=context)
                raise AppException(
                    "Внутренняя ошибка приложения",
                    status_code=500,
                    original_exc=e,
                ) from e

        return wrapper
    return decorator


class DBQueries:
    """Класс с методами для безопасной работы с базой данных (CRUD-операции)."""

    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)


    @db_operation(context="DB_SELECT")
    async def run_select(
        self,
        db: AsyncSession,
        query: str,
        params: dict | None = None,
        mode: str = "mappings_all",
        required: bool = False,
    ):
        """
        Выполняет SELECT-запрос.
        Поддерживает режимы: scalar, scalars_all, mappings_first, mappings_all, one_or_none, first
        """
        result = await db.execute(text(query), params or {})

        match mode:
            case "scalar":
                data = result.scalar()
            case "scalars_all":
                data = result.scalars().all()
            case "mappings_first":
                data = result.mappings().first()
            case "mappings_all":
                data = result.mappings().all()
            case "one_or_none":
                data = result.one_or_none()
            case "first":
                data = result.first()
            case _:
                raise AppException(f"Неизвестный режим выборки: {mode}", status_code=400)

        if required and not data:
            raise AppException("Пустой результат запроса", status_code=404)

        return data


    @db_operation(context="DB_UPDATE")
    async def run_update(
        self,
        db: AsyncSession,
        query: str,
        params: dict | None = None,
        commit: bool = True,
    ):
        """Выполняет UPDATE-запрос и возвращает количество изменённых строк."""
        result = await db.execute(text(query), params or {})
        if commit:
            await db.commit()
        return result.rowcount


    @db_operation(context="DB_INSERT")
    async def run_insert(
        self,
        db: AsyncSession,
        query: str,
        params: dict | None = None,
        commit: bool = True,
        return_id: bool = False,
    ):
        """
        Выполняет INSERT-запрос.
        Если используется RETURNING id — можно вернуть вставленный ID.
        """
        result = await db.execute(text(query), params or {})
        if commit:
            await db.commit()

        if return_id:
            inserted_id = result.scalar()
            return inserted_id if inserted_id is not None else 0

        return result.rowcount


    @db_operation(context="DB_DELETE")
    async def run_delete(
        self,
        db: AsyncSession,
        query: str,
        params: dict | None = None,
        commit: bool = True,
    ):
        """Выполняет DELETE-запрос и возвращает количество удалённых строк."""
        result = await db.execute(text(query), params or {})
        if commit:
            await db.commit()
        return result.rowcount
