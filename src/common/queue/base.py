"""Абстракция over pgqueuer для тестируемости."""

from abc import ABC, abstractmethod
from collections.abc import Callable


class AbstractQueue(ABC):
    """Абстракция over pgqueuer для тестируемости."""

    @abstractmethod
    async def enqueue(self, entrypoint: str, payload: bytes) -> None: ...
    @abstractmethod
    def register_handler(self, entrypoint: str, handler: Callable) -> None: ...
    @abstractmethod
    async def run(self) -> None: ...
    @abstractmethod
    async def stop(self) -> None: ...
