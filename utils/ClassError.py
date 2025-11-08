import logging
import asyncio
import socket
from json import JSONDecodeError
import aiohttp

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.ClassException import AppException


class ErrorInfo:
    """Модель информации об ошибке"""
    def __init__(self, message: str, type: str, level: str, context: str = ""):
        self.message = message
        self.type = type
        self.level = level
        self.context = context

    def to_dict(self):
        return {
            "error": {
                "type": self.type,
                "message": self.message,
                "level": self.level,
                "path": self.context
            }
        }


class ErrorHandler:
    """Централизованный обработчик ошибок"""
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def handle_client_error(self, e: Exception, context: str = "") -> ErrorInfo:
        """Обработка ошибок при работе с внешними клиентами"""
        if isinstance(e, asyncio.TimeoutError):
            info = ErrorInfo("Сервер не ответил вовремя", "TimeoutError", "warning", context)
        elif isinstance(e, aiohttp.ClientConnectorError):
            info = ErrorInfo("Ошибка подключения к серверу", "ClientConnectorError", "error", context)
        elif isinstance(e, aiohttp.ClientResponseError):
            info = ErrorInfo(f"Ошибка HTTP-ответа: {e.status} {e.message}", "ClientResponseError", "error", context)
        elif isinstance(e, aiohttp.ClientPayloadError):
            info = ErrorInfo("Ошибка чтения тела ответа", "ClientPayloadError", "error", context)
        elif isinstance(e, aiohttp.ClientError):
            info = ErrorInfo(f"Ошибка клиента aiohttp: {e}", "ClientError", "error", context)
        elif isinstance(e, JSONDecodeError):
            info = ErrorInfo("Ошибка декодирования JSON", "JSONDecodeError", "error", context)
        elif isinstance(e, UnicodeDecodeError):
            info = ErrorInfo("Ошибка декодирования текста", "UnicodeDecodeError", "error", context)
        elif isinstance(e, socket.gaierror):
            info = ErrorInfo("Ошибка DNS или сети", "SocketError", "error", context)
        elif isinstance(e, OSError):
            info = ErrorInfo(f"Системная ошибка ввода-вывода: {e}", "OSError", "error", context)
        elif isinstance(e, AssertionError):
            info = ErrorInfo(f"Ошибка проверки данных: {e}", "AssertionError", "error", context)
        elif isinstance(e, KeyboardInterrupt):
            info = ErrorInfo("Процесс прерван пользователем", "KeyboardInterrupt", "critical", context)
        else:
            info = ErrorInfo(f"Непредвиденная ошибка: {type(e).__name__}", "UnexpectedError", "error", context)

        self.logger.exception("Ошибка при обработке запроса", exc_info=e)
        return info

    async def handle_http_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Обработка всех HTTP и пользовательских ошибок"""
        status_code = 500
        if isinstance(exc, AppException):
            info = ErrorInfo(exc.message, exc.__class__.__name__, "warning", str(request.url))
            status_code = exc.status_code
            if exc.original_exc:
                self.logger.exception(f"[{request.url}] {exc.message}", exc_info=exc.original_exc)
            else:
                self.logger.warning(f"[{request.url}] {exc.message}")

        elif isinstance(exc, StarletteHTTPException):
            info = ErrorInfo(str(exc.detail), "HTTPException", "warning", str(request.url))
            status_code = exc.status_code
            self.logger.warning(f"[{request.url}] {exc.detail}")

        elif isinstance(exc, RequestValidationError):
            errors = []
            for err in exc.errors():
                loc = ".".join(str(x) for x in err["loc"][1:])
                msg = err["msg"].replace("Input should be", "Поле должно быть").replace(" or ", " или ")
                errors.append({"field": loc, "message": msg})
            info = ErrorInfo(errors, "ValidationError", "warning", str(request.url))
            status_code = 422
            self.logger.warning(f"[{request.url}] ValidationError: {errors}")

        elif isinstance(exc, ResponseValidationError):
            errors = []
            for err in exc.errors():
                loc = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                errors.append({"field": loc, "message": msg})
            info = ErrorInfo(errors, "ResponseValidationError", "warning", str(request.url))
            status_code = 500
            self.logger.warning(f"[{request.url}] ResponseValidationError: {errors}")

        else:
            info = ErrorInfo("Внутренняя ошибка сервера", "InternalServerError", "error", str(request.url))
            status_code = 500
            self.logger.exception(f"[{request.url}] UnexpectedError: {exc}")

        return JSONResponse(status_code=status_code, content=info.to_dict())
