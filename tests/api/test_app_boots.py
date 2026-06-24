"""App OpenAPI содержит admin_users / auth роуты."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_openapi_includes_admin_users(client: AsyncClient):
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = spec["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/admin/users" in paths
    assert "/api/v1/config" in paths
    assert "/healthcheck" in paths
