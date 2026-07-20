from typing import Any

from src.common.queue.base import AbstractQueue
from src.common.queue.pgqueuer import PgQueuerQueue


def create_queue(dsn: str, **kwargs: Any) -> AbstractQueue:
    """Фабрика очереди. ``kwargs`` пробрасываются в конструктор ``PgQueuerQueue``.

    Воркер передаёт свои Prometheus-метрики (``dispatch_up_metric`` /
    ``dispatch_restarts_metric``) и настройки супервизора; FastAPI-приложение
    зовёт без метрик — только для enqueue.
    """
    return PgQueuerQueue(dsn, **kwargs)


__all__ = ["AbstractQueue", "PgQueuerQueue", "create_queue"]
