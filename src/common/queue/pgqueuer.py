"""PgQueue - pgqueuer adapter."""

from collections.abc import Callable

import asyncpg
from pgqueuer import PgQueuer
from pgqueuer.db import AsyncpgDriver

from src.common.queue.base import AbstractQueue


class PgQueue(AbstractQueue):
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._driver: AsyncpgDriver | None = None
        self._pgq: PgQueuer | None = None
        self._handlers: dict[str, Callable] = {}

    async def _ensure(self) -> PgQueuer:
        if self._pgq is None:
            pool = await asyncpg.create_pool(self._dsn)
            self._driver = AsyncpgDriver(pool)
            self._pgq = PgQueuer(self._driver)
            for name, fn in self._handlers.items():
                self._pgq.entrypoint(name)(fn)
        return self._pgq

    async def enqueue(self, entrypoint: str, payload: bytes) -> None:
        pgq = await self._ensure()
        await pgq.queries.enqueue([entrypoint], [payload], [0])

    def register_handler(self, entrypoint: str, handler: Callable) -> None:
        self._handlers[entrypoint] = handler

    async def run(self) -> None:
        pgq = await self._ensure()
        await pgq.run()

    async def stop(self) -> None:
        if self._pgq:
            await self._pgq.shutdown()
