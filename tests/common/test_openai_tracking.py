"""TrackedOpenAI пишет usage в БД после chat-вызова."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from src.common.openai_client import TrackedOpenAI
from src.db.session import async_session_maker
from src.models.usage_log import UsageLog


@pytest.mark.asyncio
async def test_chat_create_writes_usage_log():
    # Mock AsyncOpenAI.chat.completions.create
    mock_resp = SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    )
    raw = MagicMock()
    raw.chat = MagicMock()
    raw.chat.completions = MagicMock()
    raw.chat.completions.create = AsyncMock(return_value=mock_resp)

    tracked = TrackedOpenAI(
        raw, session_factory=async_session_maker, default_model="gpt-4o-mini"
    )
    await tracked.chat.create(messages=[{"role": "user", "content": "hi"}], operation="probe")

    async with async_session_maker() as s:
        result = await s.execute(
            select(UsageLog).where(UsageLog.operation == "probe").order_by(UsageLog.id.desc())
        )
        row = result.scalar_one_or_none()
        assert row is not None
        assert row.prompt_tokens == 10
        assert row.completion_tokens == 20
        assert row.total_tokens == 30
        assert row.model == "gpt-4o-mini"
        # cleanup
        await s.delete(row)
        await s.commit()
