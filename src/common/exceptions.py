"""Базовые исключения проекта."""


class AppError(Exception):
    """Базовый класс для всех бизнес-исключений."""


class NotFoundError(AppError):
    """Ресурс не найден."""


class PermissionDeniedError(AppError):
    """Доступ запрещён."""


class ConflictError(AppError):
    """Состояние ресурса не позволяет операцию."""


class ExternalServiceError(AppError):
    """Внешний сервис (LLM, S3, OAuth) недоступен."""
