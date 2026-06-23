"""Smoke-тест: таблица users существует. Гоняется в docker compose run test."""

import pytest
from sqlalchemy import text

from src.db.session import async_session_maker


@pytest.mark.asyncio
async def test_users_table_exists():
    async with async_session_maker() as s:
        await s.execute(text("SELECT 1 FROM users LIMIT 1"))
