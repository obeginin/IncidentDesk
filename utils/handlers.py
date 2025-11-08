from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from utils.ClassConfig import logger_config

# Получаем логгер из централизованной конфигурации
logger = logger_config.get_logger("app.handlers.validation")


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Кастомная обработка ошибок валидации Pydantic, включая Enum.

    Формат ответа:
    {
      "error": {
        "type": "ValidationError",
        "message": [...],
        "level": "warning",
        "path": "..."
      }
    }
    """
    errors = []

    for err in exc.errors():
        # Пример err:
        # {'type': 'string_type', 'loc': ('body', 'field_name'), 'msg': 'Input should be a valid string', 'input': None}
        loc = ".".join(str(x) for x in err.get("loc", [])[1:])  # убираем 'body' из пути
        msg = err.get("msg", "Ошибка валидации")

        # Перевод и нормализация сообщений
        if "Input should be" in msg:
            msg = msg.replace("Input should be", "Поле должно быть").replace(" or ", " или ")
        elif "field required" in msg:
            msg = "Поле обязательно для заполнения"
        elif "none is not an allowed value" in msg:
            msg = "Поле не может быть пустым"
        elif "Input must be a valid enumeration member" in msg:
            msg = "Недопустимое значение (enum)"

        errors.append({
            "field": loc or "unknown",
            "message": msg
        })

    # --- Логируем событие ---
    logger.warning(
        f"Ошибка валидации входных данных: {errors} | "
        f"URL: {request.url.path} | Метод: {request.method}"
    )

    # --- Формируем унифицированный ответ ---
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "ValidationError",
                "message": errors,
                "level": "warning",
                "path": str(request.url)
            }
        }
    )
