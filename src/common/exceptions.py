"""Базовые исключения проекта."""


class AppError(Exception):
    """Базовый класс для всех бизнес-исключений."""


class NotFoundError(AppError):
    """Запрошенный объект не найден."""


class PermissionDeniedError(AppError):
    """Доступ запрещён."""


class ConflictError(AppError):
    """Текущее состояние объекта не позволяет выполнить операцию."""


class ExternalServiceError(AppError):
    """Внешний сервис (LLM, S3, OAuth) недоступен."""
