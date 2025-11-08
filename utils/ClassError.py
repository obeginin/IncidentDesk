
class AppException(Exception):
    """Базовое исключение приложения с HTTP статусом"""
    def __init__(self, message: str, status_code: int = 400, field: str | None = None, original_exc: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.field = field
        self.original_exc = original_exc

    def __str__(self):
        if self.original_exc:
            return f"[{self.status_code}] {self.message} — {self.original_exc!r}"
        return f"[{self.status_code}] {self.message}"

# Примеры стандартных ошибок для удобства
class BadRequest(AppException):
    def __init__(self, message: str = "Некорректный запрос", field: str | None = None):
        super().__init__(message, status_code=400, field=field)

class Unauthorized(AppException):
    def __init__(self, message: str = "Пользователь не авторизован", field: str | None = None):
        super().__init__(message, status_code=401, field=field)

class NotFound(AppException):
    def __init__(self, message: str = "Ресурс не найден", field: str | None = None):
        super().__init__(message, status_code=404, field=field)

class ConflictData(AppException):
    def __init__(self, message: str = "Конфликт данных", field: str | None = None):
        super().__init__(message, status_code=409, field=field)

class InternalServerError(AppException):
    def __init__(self, message: str = "Внутренняя ошибка сервера", field: str | None = None):
        super().__init__(message, status_code=500, field=field)
