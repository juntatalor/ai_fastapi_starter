"""Auth endpoints: /login, /me, /password."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

# NB: client + user_factory + auth_headers фикстуры появятся в tests/conftest.py
# (Chunk I). Здесь полагаемся на них; тесты будут проходить после I.1.


@pytest.mark.asyncio
async def test_login_happy(client: AsyncClient, user_factory):
    user = await user_factory(email="a@example.com", password="Secret1!")
    resp = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "Secret1!"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, user_factory):
    await user_factory(email="b@example.com", password="Secret1!")
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "b@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient, user_factory, auth_headers):
    user = await user_factory(email="c@example.com")
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(user))
    assert resp.status_code == 200
    assert resp.json()["email"] == user.email


@pytest.mark.asyncio
async def test_password_change_happy(client: AsyncClient, user_factory, auth_headers):
    user = await user_factory(email="d@example.com", password="Old1!aaa")
    resp = await client.post(
        "/api/v1/auth/password",
        headers=auth_headers(user),
        json={"current_password": "Old1!aaa", "new_password": "Newpassword!1"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_password_change_wrong_current(client: AsyncClient, user_factory, auth_headers):
    user = await user_factory(email="e@example.com", password="Old1!aaa")
    resp = await client.post(
        "/api/v1/auth/password",
        headers=auth_headers(user),
        json={"current_password": "wrong", "new_password": "Newpassword!1"},
    )
    assert resp.status_code == 400
