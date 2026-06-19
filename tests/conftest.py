"""Глобальные фикстуры: async DB session + httpx AsyncClient + helpers."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Гарантируем что Settings прочитают тестовые значения — до импорта src.config.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/app_test"
)
os.environ.setdefault("JWT_SECRET", "test-secret-32-chars-min-padding-aaa")
os.environ.setdefault("YANDEX_OAUTH_ENABLED", "false")
os.environ.setdefault("OPENAI_API_KEY", "test-fake")
os.environ.setdefault("S3_ENDPOINT_URL", "http://minio:9000")
os.environ.setdefault("S3_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "minioadmin")
os.environ.setdefault("S3_BUCKET_NAME", "app-test")

from src.config import get_settings  # noqa: E402
from src.db import session as db_session_module  # noqa: E402
from src.main import create_app  # noqa: E402
from src.models.user import User, UserRole  # noqa: E402
from src.services.auth import hash_password, issue_token  # noqa: E402

_settings = get_settings()
_engine = create_async_engine(_settings.database_url, future=True)
_TestSession = async_sessionmaker(_engine, expire_on_commit=False)

# Подмена sessionmaker в src.db.session чтобы dependency get_db брал тестовую БД
# (на случай если settings prod-евые перехватываются после import).
db_session_module.engine = _engine
db_session_module.async_session_maker = _TestSession


@pytest_asyncio.fixture(autouse=True)
async def _clean_db() -> AsyncIterator[None]:
    """Каждый тест начинается с пустых таблиц."""
    async with _engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE usage_log, users RESTART IDENTITY CASCADE"))
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with _TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def user_factory(db_session: AsyncSession) -> Callable:
    async def _make(
        *,
        email: str,
        role: UserRole = UserRole.USER,
        password: str | None = "Password1!",
        full_name: str | None = None,
    ) -> User:
        u = User(
            email=email,
            full_name=full_name or email.split("@")[0],
            role=role,
            password_hash=hash_password(password) if password else None,
            is_active=True,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        return u

    return _make


@pytest.fixture
def auth_headers() -> Callable[[User], dict[str, str]]:
    def _make(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {issue_token(user.id)}"}

    return _make
