"""AppSettings — env-driven config (Pydantic v2)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Конфиг FastAPI-приложения. Читается из env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="ai_fastapi_starter", description="Имя сервиса для логов и UI.")
    debug: bool = Field(default=False, description="SQL-echo, verbose-логи.")
    app_base_url: str = Field(
        default="http://localhost:8000",
        description="Public URL приложения (для OAuth redirect и т. п.).",
    )
    log_level: str = Field(default="INFO", description="Уровень логирования.")

    database_url: str = Field(description="postgresql+asyncpg DSN.")

    jwt_secret: str = Field(min_length=32, description="HMAC ключ для JWT.")
    jwt_ttl_days: int = Field(default=7, ge=1, le=90, description="Срок жизни access token.")

    yandex_oauth_enabled: bool = Field(default=False, description="Kill-switch Yandex OAuth.")
    yandex_client_id: str = Field(default="", description="ClientID из ya.console.")
    yandex_client_secret: str = Field(default="", description="ClientSecret.")
    yandex_redirect_uri: str = Field(
        default="http://localhost:5173/oauth/yandex",
        description="Куда Yandex возвращает code (frontend route).",
    )

    openai_api_key: str = Field(default="", description="OpenAI / compat API key.")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL для OpenAI-совместимого провайдера.",
    )
    openai_default_model: str = Field(default="gpt-4o-mini", description="Дефолт LLM-модели.")
    openai_chat_timeout_seconds: float = Field(default=60.0, ge=1.0, le=600.0)

    s3_endpoint_url: str = Field(default="http://localhost:9000")
    s3_access_key_id: str = Field(default="")
    s3_secret_access_key: str = Field(default="")
    s3_bucket_name: str = Field(default="app")
    s3_region: str = Field(default="us-east-1")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()  # type: ignore[call-arg]
