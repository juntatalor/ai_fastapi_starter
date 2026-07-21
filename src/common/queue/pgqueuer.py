"""Реализация очереди на базе pgqueuer, поднимает встроенный супервизор
для авторестарта consumer.

Managed Postgres / прокси рвут долгоживущие asyncpg-коннекты по
idle-timeout. Голый ``pgq.run()`` тогда падает
``asyncpg.InterfaceError: connection is closed`` — dispatch умирает,
задачи копятся, никто не замечает пока не прилетит алерт по очереди.

Consumer поэтому крутится в цикле супервизора (:meth:`_supervise`): при
любой ошибке пересоздаём коннект, PgQueuer и entrypoint-байндинги, ждём
``dispatch_retry_seconds`` и стартуем dispatch снова. Метрики
``dispatch_up`` / ``dispatch_restarts`` инжектируются извне — иначе
пришлось бы тянуть воркеровые метрики в common.

Producer работает через отдельный коннект (asyncpg не поддерживает
конкурентные операции на одном коннекте). :meth:`enqueue` ретраится
на ``InterfaceError``, пересоздавая producer-коннект — тот же сценарий
idle-таймаута, только без супервизора вокруг.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

import asyncpg  # type: ignore[import-untyped]
from pgqueuer import PgQueuer
from pgqueuer.domain.models import Job
from prometheus_client import Counter, Gauge

from src.common.queue.base import AbstractQueue, JobHandler
from src.common.retry import retry_async

logger = logging.getLogger(__name__)


class PgQueuerQueue(AbstractQueue):
    """PgQueuer + супервизор + enqueue-reconnect.

    Параметры фабрики (:func:`src.common.queue.create_queue`) — под DI:
    ``dispatch_retry_seconds`` — пауза между рестартами цикла consumer,
    ``reconnect_attempts`` — сколько раз пытаться реконнектнуть producer
    в одном ``enqueue()``, ``dispatch_up_metric`` /
    ``dispatch_restarts_metric`` — Prometheus-метрики воркера.
    """

    def __init__(
        self,
        dsn: str,
        *,
        dispatch_retry_seconds: int = 15,
        reconnect_attempts: int = 2,
        dispatch_up_metric: Gauge | None = None,
        dispatch_restarts_metric: Counter | None = None,
    ) -> None:
        self._dsn = dsn
        self._handlers: dict[str, JobHandler] = {}
        self._pgq: PgQueuer | None = None
        self._conn: asyncpg.Connection | None = None
        self._producer_conn: asyncpg.Connection | None = None
        self._supervisor_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._dispatch_retry_seconds = dispatch_retry_seconds
        self._reconnect_attempts = reconnect_attempts
        self._dispatch_up = dispatch_up_metric
        self._dispatch_restarts = dispatch_restarts_metric

    def register_handler(self, entrypoint: str, handler: JobHandler) -> None:
        self._handlers[entrypoint] = handler

    # ---------- producer ----------

    async def _ensure_producer(self) -> asyncpg.Connection:
        """Отдельное соединение для постановки задач.

        Пересоздаёт коннект если он закрыт — long-lived asyncpg рвётся по
        idle timeout от managed Postgres, следующий enqueue упадёт
        InterfaceError без переподключения.
        """
        if self._producer_conn is None or self._producer_conn.is_closed():
            self._producer_conn = await asyncpg.connect(self._dsn)
        return self._producer_conn

    async def _reset_producer(self) -> None:
        if self._producer_conn is not None:
            with contextlib.suppress(Exception):
                await self._producer_conn.close()
        self._producer_conn = None

    async def enqueue(self, entrypoint: str, payload: bytes, priority: int = 0) -> None:
        async def _attempt() -> None:
            conn = await self._ensure_producer()
            pgq = PgQueuer.from_asyncpg_connection(conn)
            # pgq.queries тип-хинтится как RepositoryPort | None, но в свежесозданном
            # PgQueuer он всегда есть — pgqueuer стабов пока не отдаёт.
            assert pgq.queries is not None
            await pgq.queries.enqueue([entrypoint], [payload], [priority])

        async def _on_retry(exc: BaseException, attempt: int) -> None:
            logger.warning(
                "pgqueuer enqueue attempt=%d failed (%s), reconnecting", attempt, exc
            )
            await self._reset_producer()

        await retry_async(
            _attempt,
            attempts=self._reconnect_attempts,
            exceptions=(asyncpg.exceptions.InterfaceError, ConnectionError),
            on_retry=_on_retry,
        )

    # ---------- consumer supervisor ----------

    async def start(self) -> None:
        """Стартует супервизор consumer в фоне. Идемпотентно."""
        if self._supervisor_task is not None and not self._supervisor_task.done():
            return
        self._stop_event = asyncio.Event()
        self._supervisor_task = asyncio.create_task(self._supervise())
        logger.info("PgQueuerQueue supervisor started")

    async def _supervise(self) -> None:
        """Крутит consumer в вечном цикле, перезапускает после сбоя.

        Инвариант: между итерациями ``dispatch_up=1`` (в фазе ``pgq.run``)
        либо ``dispatch_up=0`` (ждём retry). Cancel супервизора → штатный
        выход через ``stop_event``, метрика в 0.
        """
        while not self._stop_event.is_set():
            try:
                # Каждая итерация — свежий коннект: старый мог быть закрыт
                # на стороне PG после разрыва, реюзать нельзя.
                await self._close_consumer_conn()
                self._conn = await asyncpg.connect(self._dsn)
                self._pgq = PgQueuer.from_asyncpg_connection(self._conn)
                for entrypoint, handler in self._handlers.items():
                    self._bind_handler(entrypoint, handler)
                logger.info("PgQueuerQueue dispatch loop starting")
                if self._dispatch_up is not None:
                    self._dispatch_up.set(1)
                await self._pgq.run()
                logger.info("PgQueuerQueue dispatch loop returned normally")
            except asyncio.CancelledError:
                logger.info("PgQueuerQueue supervisor cancelled")
                raise
            except Exception:
                logger.exception(
                    "pgqueuer dispatch loop crashed, restart через %ds",
                    self._dispatch_retry_seconds,
                )
                if self._dispatch_restarts is not None:
                    self._dispatch_restarts.inc()
            finally:
                if self._dispatch_up is not None:
                    self._dispatch_up.set(0)
            # Прерываемая пауза: если во время sleep словили stop_event.set()
            # — выйдем сразу, без ожидания дожатия таймера.
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._dispatch_retry_seconds,
                )

    async def _close_consumer_conn(self) -> None:
        """Закрыть текущий consumer-коннект. Ошибки при close игнорируются —
        коннект уже мог быть разорван на стороне сервера."""
        if self._conn is not None:
            with contextlib.suppress(Exception):
                await self._conn.close()
        self._conn = None
        self._pgq = None

    def _bind_handler(self, entrypoint: str, handler: JobHandler) -> None:
        """Регистрирует обработчик в pgqueuer entrypoint."""
        assert self._pgq is not None

        @self._pgq.entrypoint(entrypoint)
        async def _h(job: Job) -> None:
            # pgqueuer тип-хинтит job.payload как bytes | None, но on-disk он
            # хранит именно то что мы отдали в enqueue() — там bytes всегда.
            assert job.payload is not None
            await handler(job.payload)

    async def stop(self) -> None:
        """Отменяет супервизор и закрывает соединения."""
        self._stop_event.set()
        if self._supervisor_task:
            self._supervisor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._supervisor_task
        await self._close_consumer_conn()
        if self._producer_conn is not None:
            with contextlib.suppress(Exception):
                await self._producer_conn.close()
        self._producer_conn = None
        if self._dispatch_up is not None:
            self._dispatch_up.set(0)
        logger.info("PgQueuerQueue stopped")
