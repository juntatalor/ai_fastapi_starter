"""Public config endpoint отдаёт app_name + yandex_enabled."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_config_returns_yandex_flag(client: AsyncClient, monkeypatch):
    monkeypatch.setenv("YANDEX_OAUTH_ENABLED", "true")
    from src.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    resp = await client.get("/api/v1/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["yandex_enabled"] is True
    assert "app_name" in body


@pytest.mark.asyncio
async def test_config_disabled_flag(client: AsyncClient, monkeypatch):
    monkeypatch.setenv("YANDEX_OAUTH_ENABLED", "false")
    from src.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    resp = await client.get("/api/v1/config")
    assert resp.status_code == 200
    assert resp.json()["yandex_enabled"] is False
