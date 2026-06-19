"""Yandex /start /callback + флаг-гейтинг."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from src.services.yandex_oauth import YandexUserInfo


@pytest.mark.asyncio
async def test_disabled_returns_404(client: AsyncClient, monkeypatch):
    monkeypatch.setenv("YANDEX_OAUTH_ENABLED", "false")
    from src.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    resp = await client.get("/api/v1/auth/yandex/start", follow_redirects=False)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_callback_links_existing_user(client: AsyncClient, user_factory, monkeypatch):
    monkeypatch.setenv("YANDEX_OAUTH_ENABLED", "true")
    from src.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    user = await user_factory(email="z@example.com")
    info = YandexUserInfo(yandex_id="99", email=user.email, display_name="Z")
    with patch("src.api.routes.v1.auth.exchange_code", return_value=info):
        resp = await client.get("/api/v1/auth/yandex/callback?code=abc")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_callback_unknown_email_403(client: AsyncClient, monkeypatch):
    monkeypatch.setenv("YANDEX_OAUTH_ENABLED", "true")
    from src.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    info = YandexUserInfo(yandex_id="99", email="ghost@example.com", display_name="G")
    with patch("src.api.routes.v1.auth.exchange_code", return_value=info):
        resp = await client.get("/api/v1/auth/yandex/callback?code=abc")
    assert resp.status_code == 403
