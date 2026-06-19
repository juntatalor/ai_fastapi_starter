from src.common.queue.base import AbstractQueue
from src.common.queue.pgqueuer import PgQueue


def create_queue(dsn: str) -> AbstractQueue:
    return PgQueue(dsn)


__all__ = ["AbstractQueue", "PgQueue", "create_queue"]
