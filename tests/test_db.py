"""Smoke-тест: таблица users существует в тестовой БД."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_users_table_exists(db_session: AsyncSession) -> None:
    await db_session.execute(text("SELECT 1 FROM users LIMIT 1"))
