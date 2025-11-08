# Incident Desk Service

Сервис для учёта инцидентов с REST API, логированием и мониторингом состояния.

## Запуск через Docker

1. Создайте `.env` файл в корне проекта (пример ниже):

```env
APP_NAME=incident_desk
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=false
SECRET_KEY=secret_wallet_key_2341111111

DB_HOST=db
DB_PORT=5432
DB_USER=sa
DB_PASS=1111
DB_NAME=incidents_db

DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

LOG_LEVEL=INFO
LOG_FILE=logs

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

API_PREFIX=/api/v1
TIMEZONE=Europe/Moscow
```

2. Сборка и запуск контейнеров:

```bash
docker compose -f docker-compose.yml up -d --build 
```

3. Логи приложения:

```bash
docker logs -f incident_desk
```

4. Остановка контейнеров:

```bash
docker compose down
```

---

## API Эндпоинты

### Инциденты

* **POST /api/v1/incidents** — создание инцидента

Пример запроса:

```json
{
  "description": "Сбой в системе",
  "source": "monitoring"
}
```

* **GET /api/v1/incidents** — список инцидентов (опционально фильтр по статусу)

Пример запроса:

```
/api/v1/incidents?status=new
```

* **PATCH /api/v1/incidents/{incident_id}/status** — обновление статуса инцидента

Пример запроса:

```json
{
  "status": "resolved"
}
```

### Мониторинг

* **GET /api/v1/monitoring/incidents** — статистика по инцидентам (количество по статусам)

Пример ответа:

```json
{
  "new": 5,
  "in_progress": 2,
  "resolved": 10
}
```

### Health Check

* **GET /api/health** — проверка состояния сервиса и подключения к БД

Пример ответа:

```json
{
  "status": "healthy",
  "service": "incident_desk",
  "version": "1.0.0",
  "environment": "development",
  "debug": false,
  "uptime_seconds": 120
}
```
