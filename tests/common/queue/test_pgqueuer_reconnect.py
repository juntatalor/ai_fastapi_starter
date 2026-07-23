"""Тест автопереподключения в PgQueuerQueue.enqueue.

Прод-сценарий: pgqueuer держит долгоживущий asyncpg-коннект, managed
Postgres / прокси убил коннект по idle timeout — следующий enqueue должен
переподнять коннект через on_retry, чтобы клиент не получил 500.
"""

from __future__ import annotations

import asyncpg  # type: ignore[import-untyped]
import pytest

from src.common.queue.pgqueuer import PgQueuerQueue


@pytest.mark.asyncio
async def test_enqueue_propagates_when_reconnect_also_fails(monkeypatch) -> None:
    """Если коннект мёртв и переподнять не удаётся — пробрасываем исключение
    после исчерпания всех попыток (reconnect_attempts из настроек)."""
    queue = PgQueuerQueue(
        "postgresql://nohost.invalid:5432/none",
        reconnect_attempts=3,
    )

    call_count = {"n": 0}

    async def fake_connect(*_args, **_kwargs):
        call_count["n"] += 1
        raise asyncpg.exceptions.InterfaceError("simulated connect failure")

    monkeypatch.setattr(asyncpg, "connect", fake_connect)

    with pytest.raises(asyncpg.exceptions.InterfaceError):
        await queue.enqueue("noop", b"x")
    # Количество попыток = reconnect_attempts (передали 3).
    assert call_count["n"] == 3
