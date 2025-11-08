
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


class BadRequest(AppException):
    def __init__(self, message="Некорректный запрос", field=None):
        super().__init__(message, 400, field)


class Unauthorized(AppException):
    def __init__(self, message="Пользователь не авторизован", field=None):
        super().__init__(message, 401, field)


class NotFound(AppException):
    def __init__(self, message="Ресурс не найден", field=None):
        super().__init__(message, 404, field)


class ConflictData(AppException):
    def __init__(self, message="Конфликт данных", field=None):
        super().__init__(message, 409, field)


class InternalServerError(AppException):
    def __init__(self, message="Внутренняя ошибка сервера", field=None):
        super().__init__(message, 500, field)
