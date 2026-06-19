"""Глобальные фикстуры: async DB session + httpx AsyncClient + helpers.

Архитектура: per-test event loop (default pytest-asyncio function-scope).
Engine создаётся **внутри** каждой фикстуры — таким образом asyncpg
connection не пересекается между loops.

Чтобы FastAPI dependency ``get_db`` использовал тестовый engine, делаем
``app.dependency_overrides[get_db] = lambda: <test session>``.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Гарантируем что Settings прочитают тестовые значения — до импорта src.config.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/app_test")
os.environ.setdefault("JWT_SECRET", "test-secret-32-chars-min-padding-aaa")
os.environ.setdefault("YANDEX_OAUTH_ENABLED", "false")
os.environ.setdefault("OPENAI_API_KEY", "test-fake")
os.environ.setdefault("S3_ENDPOINT_URL", "http://minio:9000")
os.environ.setdefault("S3_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "minioadmin")
os.environ.setdefault("S3_BUCKET_NAME", "app-test")

from src.api.deps import get_db  # noqa: E402
from src.config import get_settings  # noqa: E402
from src.db.session import Base  # noqa: E402
from src.main import create_app  # noqa: E402
from src.models import *  # noqa: E402,F401,F403 — регистрирует все модели в Base.metadata
from src.models.user import User, UserRole  # noqa: E402
from src.services.auth import hash_password, issue_token  # noqa: E402

_SCHEMA_INITIALIZED = False


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator:
    """Создаёт async engine на текущий event-loop теста.

    NullPool — не кешируем соединения между тестами.
    Schema создаётся один раз (модуль-flag).
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True, poolclass=NullPool)
    global _SCHEMA_INITIALIZED
    if not _SCHEMA_INITIALIZED:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _SCHEMA_INITIALIZED = True
    # Чистим таблицы перед каждым тестом.
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM usage_log"))
        await conn.execute(text("DELETE FROM users"))
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    """Сессия для прямого использования из теста (например user_factory)."""
    Session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with Session() as s:
        yield s


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncIterator[AsyncClient]:
    """HTTP client с FastAPI dependency_overrides на тестовый engine."""
    app = create_app()
    Session = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        async with Session() as s:
            yield s

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def user_factory(db_session: AsyncSession) -> Callable:
    """Фабрика юзеров. Использует db_session (тот же engine что и client)."""

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
