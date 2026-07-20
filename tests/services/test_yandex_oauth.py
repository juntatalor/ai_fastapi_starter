"""Yandex OAuth service: mock httpx for token/info exchange."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from src.services.yandex_oauth import exchange_code


@pytest.mark.asyncio
async def test_exchange_code_returns_user_info(monkeypatch):
    monkeypatch.setenv("YANDEX_CLIENT_ID", "client")
    monkeypatch.setenv("YANDEX_CLIENT_SECRET", "secret")
    from src.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]

    with respx.mock(assert_all_called=True) as m:
        m.post("https://oauth.yandex.ru/token").mock(
            return_value=Response(200, json={"access_token": "tok"})
        )
        m.get("https://login.yandex.ru/info").mock(
            return_value=Response(
                200,
                json={"id": "42", "default_email": "a@example.com", "real_name": "Alice"},
            )
        )
        info = await exchange_code("code123")
    assert info.yandex_id == "42"
    assert info.email == "a@example.com"
    assert info.display_name == "Alice"
