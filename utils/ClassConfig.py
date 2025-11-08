from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str
    APP_VERSION: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., min_length=16)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300

    # Database
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    @computed_field
    @property
    def ASYNC_DB_URL(self) -> str:
        'Ассинхронное подключение'
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    '''
    Синхронное подключение
    @property
    def DB_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"'''

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"

    PROJECT_ROOT: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    LOG_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "logs")

    API_PREFIX: str = "/api/v1"
    TIMEZONE: str = "Europe/Moscow"


    def create_dirs(self):
        """Создание директорий после инициализации"""
        for folder in [self.LOG_DIR, self.UPLOADS_DIR]:
            folder.mkdir(parents=True, exist_ok=True)

    def dump(self):
        """Вывод основных настроек в лог"""
        return {
            "APP_NAME": self.APP_NAME,
            "ENVIRONMENT": self.ENVIRONMENT,
            "DEBUG": self.DEBUG,
            "DB_HOST": self.DB_HOST,
            "DB_NAME": self.DB_NAME,
            "LOG_DIR": str(self.LOG_DIR),
            "API_PREFIX": self.API_PREFIX,
        }

settings = Settings()
