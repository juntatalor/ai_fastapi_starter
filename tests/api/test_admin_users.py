"""Admin /users CRUD tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from src.models.user import UserRole


@pytest.mark.asyncio
async def test_non_admin_gets_403(client: AsyncClient, user_factory, auth_headers):
    user = await user_factory(email="u1@example.com", role=UserRole.USER)
    resp = await client.get("/api/v1/admin/users", headers=auth_headers(user))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list(client: AsyncClient, user_factory, auth_headers):
    admin = await user_factory(email="a1@example.com", role=UserRole.ADMIN)
    resp = await client.get("/api/v1/admin/users", headers=auth_headers(admin))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_admin_can_create(client: AsyncClient, user_factory, auth_headers):
    admin = await user_factory(email="a2@example.com", role=UserRole.ADMIN)
    resp = await client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin),
        json={"email": "newbie@example.com", "role": "user", "password": "Initial!1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newbie@example.com"
    assert body["has_password"] is True


@pytest.mark.asyncio
async def test_create_duplicate_409(client: AsyncClient, user_factory, auth_headers):
    admin = await user_factory(email="a3@example.com", role=UserRole.ADMIN)
    await user_factory(email="dup@example.com")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin),
        json={"email": "dup@example.com", "role": "user"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_role(client: AsyncClient, user_factory, auth_headers):
    admin = await user_factory(email="a4@example.com", role=UserRole.ADMIN)
    target = await user_factory(email="t1@example.com")
    resp = await client.patch(
        f"/api/v1/admin/users/{target.id}",
        headers=auth_headers(admin),
        json={"role": "admin"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_reset_password(client: AsyncClient, user_factory, auth_headers):
    admin = await user_factory(email="a5@example.com", role=UserRole.ADMIN)
    target = await user_factory(email="t2@example.com")
    resp = await client.post(
        f"/api/v1/admin/users/{target.id}/password",
        headers=auth_headers(admin),
        json={"new_password": "Reset!Word1"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_soft_delete(client: AsyncClient, user_factory, auth_headers):
    admin = await user_factory(email="a6@example.com", role=UserRole.ADMIN)
    target = await user_factory(email="t3@example.com")
    resp = await client.delete(
        f"/api/v1/admin/users/{target.id}",
        headers=auth_headers(admin),
    )
    assert resp.status_code == 204
