"""Конфигурация логирования приложения.

Портировано из hrai с минимальными правками под стартер.

Поддерживает два форматтера:
- ``default`` — читаемый текст для разработки (DEBUG=true)
- ``json`` — однострочный JSON для прода (DEBUG=false), удобен для Loki/CloudWatch

Библиотечные логгеры явно перечислены: handlers=[], propagate=True.
Это гарантирует единый формат — все записи идут через root-хендлер с нашим форматтером.

``ContextFilter`` автоматически добавляет ``request_id`` / ``user_id`` /
``operation`` из contextvars (см. ``src/context.py``) в каждую запись лога.
"""

import copy
import json
import logging
from typing import Any

# Библиотечные логгеры, которые нужно нормализовать под наш формат.
# Если будешь подключать новую библиотеку с шумным логгером — добавь её сюда.
_LIBRARY_LOGGERS: list[str] = [
    "uvicorn",
    "uvicorn.error",
    "sqlalchemy",
    "sqlalchemy.engine",
    "asyncpg",
    "pgqueuer",
    "aioboto3",
    "aiobotocore",
    "botocore",
    "openai",
    "httpx",
]

_DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "context": {
            "()": "src.common.logging_config.ContextFilter",
        },
    },
    "formatters": {
        "default": {
            "format": (
                "%(asctime)s | %(levelname)-8s | %(request_id)s"
                " | %(user_id)s | %(name)s | %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "src.common.logging_config.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "filters": ["context"],
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        # Свой код — DEBUG чтобы видеть отладку.
        "src": {"level": "DEBUG", "propagate": True},
        # Uvicorn — снимаем его хендлеры, пропускаем через root.
        "uvicorn": {"handlers": [], "level": "INFO", "propagate": True},
        "uvicorn.access": {"handlers": [], "level": "WARNING", "propagate": False},
        "uvicorn.error": {"handlers": [], "level": "INFO", "propagate": True},
        # Библиотеки — WARNING чтобы не спамили в INFO.
        "sqlalchemy": {"handlers": [], "level": "WARNING", "propagate": True},
        "sqlalchemy.engine": {"handlers": [], "level": "WARNING", "propagate": True},
        "asyncpg": {"handlers": [], "level": "WARNING", "propagate": True},
        "pgqueuer": {"handlers": [], "level": "INFO", "propagate": True},
        "aioboto3": {"handlers": [], "level": "WARNING", "propagate": True},
        "aiobotocore": {"handlers": [], "level": "WARNING", "propagate": True},
        "botocore": {"handlers": [], "level": "WARNING", "propagate": True},
        "openai": {"handlers": [], "level": "WARNING", "propagate": True},
        "httpx": {"handlers": [], "level": "WARNING", "propagate": True},
    },
}


class ContextFilter(logging.Filter):
    """Добавляет request_id / user_id / operation из contextvars в запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Импорт внутри метода — модуль logging_config может грузиться раньше
        # чем src.context (например через dictConfig строкой-классом).
        from src.context import current_operation, request_id, user_id

        record.request_id = request_id.get() or "-"
        record.user_id = user_id.get() or "-"
        op = current_operation.get()
        if op:
            record.operation = op
        return True


class JsonFormatter(logging.Formatter):
    """Форматтер для продакшн-логов: одна строка JSON на запись."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if (rid := getattr(record, "request_id", "")) and rid != "-":
            log_data["request_id"] = rid
        if (uid := getattr(record, "user_id", "")) and uid != "-":
            log_data["user_id"] = uid
        if op := getattr(record, "operation", ""):
            log_data["operation"] = op
        if record.exc_info:
            log_data["exc"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Рекурсивно мержит ``override`` в ``base``, возвращая новый словарь.

    Вложенные dict мержатся рекурсивно; остальные значения заменяются.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_logging_config(
    level: str = "INFO",
    *,
    debug: bool = False,
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Возвращает итоговый конфиг для ``logging.config.dictConfig``.

    Args:
        level: корневой уровень логирования, например ``"INFO"``.
        debug: ``True`` — читаемый текстовый форматтер, иначе JSON.
        override: словарь, глубоко смерджённый поверх дефолтного конфига
            (для добавления своих логгеров / handler'ов в конкретном проекте).
    """
    config = copy.deepcopy(_DEFAULT_CONFIG)
    config["handlers"]["console"]["formatter"] = "default" if debug else "json"
    config["root"]["level"] = level
    if override:
        return deep_merge(config, override)
    return config
