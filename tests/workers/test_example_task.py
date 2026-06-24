"""example_task: payload парсится и handler пишет в лог."""

from __future__ import annotations

import logging

import pytest

from src.workers.worker.tasks.example_task import handle_example


@pytest.mark.asyncio
async def test_handle_example_logs(caplog):
    caplog.set_level(logging.INFO)
    await handle_example(b'{"message": "hi"}')
    assert any("hi" in r.message for r in caplog.records)
