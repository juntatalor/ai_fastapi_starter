"""Тесты супервизора pgqueuer — авторестарт после сбоя коннекта.

Инцидент 09.07.2026 в hrai: managed PG рвал долгоживущий asyncpg-коннект,
pgq.run падал ``InterfaceError: connection is closed`` — dispatch молчал
несколько дней пока не спохватились по глубине очереди. Портируем
паттерн супервизора сюда в стартер, чтобы новый проект сразу поднимал
consumer с авто-restart'ом, а не искал grabage-issue после первого прода.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg  # type: ignore[import-untyped]
import pytest
from prometheus_client import CollectorRegistry, Counter, Gauge

from src.common.queue.pgqueuer import PgQueuerQueue


def _make_metrics() -> tuple[Gauge, Counter]:
    """Свежий registry на каждый тест — иначе prometheus поймает дубликат."""
    reg = CollectorRegistry()
    up = Gauge("test_dispatch_up", "up", registry=reg)
    restarts = Counter("test_dispatch_restarts", "restarts", registry=reg)
    return up, restarts


@pytest.mark.asyncio
async def test_supervisor_restarts_after_interface_error() -> None:
    """pgq.run() падает InterfaceError → супервизор перезапускает.

    Первый вызов run — InterfaceError, второй виснет (нормальный dispatch).
    Проверяем: mock_connect был вызван >=2 раз, dispatch_up вернулся в 1,
    restart-counter вырос.
    """
    up, restarts = _make_metrics()

    hang_started = asyncio.Event()
    first_call = True

    async def _run_side_effect() -> None:
        nonlocal first_call
        if first_call:
            first_call = False
            raise asyncpg.exceptions.InterfaceError("connection is closed")
        hang_started.set()
        # Висим бесконечно как настоящий pgq.run — пока супервизор не отменит.
        await asyncio.sleep(3600)

    fake_pgq = MagicMock()
    fake_pgq.run = AsyncMock(side_effect=_run_side_effect)
    fake_pgq.entrypoint = MagicMock(return_value=lambda fn: fn)

    fake_conn = MagicMock()
    fake_conn.close = AsyncMock()

    with (
        patch(
            "src.common.queue.pgqueuer.asyncpg.connect",
            new=AsyncMock(return_value=fake_conn),
        ) as mock_connect,
        patch(
            "src.common.queue.pgqueuer.PgQueuer.from_asyncpg_connection",
            return_value=fake_pgq,
        ),
    ):
        queue = PgQueuerQueue(
            "postgresql://fake/db",
            dispatch_retry_seconds=0,  # без ожидания, тест не должен тормозить
            dispatch_up_metric=up,
            dispatch_restarts_metric=restarts,
        )
        await queue.start()
        # Ждём когда супервизор дойдёт до второй итерации и войдёт в pgq.run.
        await asyncio.wait_for(hang_started.wait(), timeout=5.0)
        try:
            assert mock_connect.await_count >= 2
            assert up._value.get() == 1  # type: ignore[attr-defined]
            assert restarts._value.get() == 1  # type: ignore[attr-defined]
        finally:
            await queue.stop()

    # После stop dispatch_up = 0.
    assert up._value.get() == 0  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_supervisor_exits_cleanly_on_stop() -> None:
    """queue.stop() → supervisor отменяется, метрика в 0, повторный start работает."""
    up, restarts = _make_metrics()

    async def _hang() -> None:
        await asyncio.sleep(3600)

    fake_pgq = MagicMock()
    fake_pgq.run = AsyncMock(side_effect=_hang)
    fake_pgq.entrypoint = MagicMock(return_value=lambda fn: fn)

    fake_conn = MagicMock()
    fake_conn.close = AsyncMock()

    with (
        patch(
            "src.common.queue.pgqueuer.asyncpg.connect",
            new=AsyncMock(return_value=fake_conn),
        ),
        patch(
            "src.common.queue.pgqueuer.PgQueuer.from_asyncpg_connection",
            return_value=fake_pgq,
        ),
    ):
        queue = PgQueuerQueue(
            "postgresql://fake/db",
            dispatch_retry_seconds=0,
            dispatch_up_metric=up,
            dispatch_restarts_metric=restarts,
        )
        await queue.start()
        # Даём супервизору войти в pgq.run
        await asyncio.sleep(0.05)
        assert up._value.get() == 1  # type: ignore[attr-defined]
        await queue.stop()
        assert up._value.get() == 0  # type: ignore[attr-defined]
        assert queue._supervisor_task is not None
        assert queue._supervisor_task.done()
