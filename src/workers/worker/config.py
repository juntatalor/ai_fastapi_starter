"""WorkerSettings — независимая от AppSettings конфигурация."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    pgqueuer_dsn: str
    worker_metrics_port: int = Field(default=8001, ge=1024, le=65535)
    pgqueuer_dispatch_retry_seconds: int = Field(
        default=15,
        ge=1,
        le=600,
        description="Пауза между рестартами цикла consumer в супервизоре.",
    )
    pgqueuer_reconnect_attempts: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Сколько попыток на один enqueue при InterfaceError producer-коннекта.",
    )
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_default_model: str = "gpt-4o-mini"
    log_level: str = "INFO"


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()  # type: ignore[call-arg]
