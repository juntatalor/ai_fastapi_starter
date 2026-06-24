"""Healthcheck вернёт {"status": "ok"} с 200."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_returns_ok(client: AsyncClient):
    resp = await client.get("/healthcheck")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
