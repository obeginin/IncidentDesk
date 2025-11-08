import logging
import asyncio
import socket
from json import JSONDecodeError
import aiohttp

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.ClassError import AppException

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

    # Клиентские асинхронные ошибки (aiohttp / asyncio / socket)
    async def handle_client_error(self, e: Exception, context: str = "") -> ErrorInfo:
        """Обработка ошибок при работе с внешними асинхронными клиентами"""
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
            info = ErrorInfo(f"Непредвиденная ошибка: {type(e).__name__} — {e}", "UnexpectedError", "error", context)

        # логирование
        getattr(self.logger, info.level, self.logger.error)(f"[{info.context}] {info.message}")
        return info


    async def handle_http_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Обработка ошибок FastAPI / HTTP / валидации"""
        if isinstance(exc, AppException):
            info = ErrorInfo(exc.message, exc.__class__.__name__, "warning", str(request.url))
            status_code = exc.status_code
        elif isinstance(exc, StarletteHTTPException):
            info = ErrorInfo(str(exc.detail), "HTTPException", "warning", str(request.url))
            status_code = exc.status_code
        elif isinstance(exc, RequestValidationError):
            info = ErrorInfo("Ошибка валидации запроса", "ValidationError", "warning", str(request.url))
            status_code = 422
        else:
            info = ErrorInfo(f"Непредвиденная ошибка: {type(exc).__name__} — {exc}", "UnexpectedError", "error", str(request.url))
            status_code = 500

        # логирование
        getattr(self.logger, info.level, self.logger.error)(f"[{info.context}] {info.message}")

        return JSONResponse(
            status_code=status_code,
            content=info.to_dict()
        )