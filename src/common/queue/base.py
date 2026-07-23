"""Абстракция over pgqueuer для тестируемости."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

JobHandler = Callable[[bytes], Awaitable[None]]


class AbstractQueue(ABC):
    """Очередь задач: producer (``enqueue``) + фоновой consumer (``start/stop``).

    ``start()`` поднимает supervisor в фоне — не блокирует. Consumer-loop
    внутри сам ловит потерю коннекта и перезапускает dispatch. ``stop()`` —
    штатное завершение, отменяет супервизор.
    """

    @abstractmethod
    async def enqueue(self, entrypoint: str, payload: bytes, priority: int = 0) -> None: ...
    @abstractmethod
    def register_handler(self, entrypoint: str, handler: JobHandler) -> None: ...
    @abstractmethod
    async def start(self) -> None: ...
    @abstractmethod
    async def stop(self) -> None: ...
