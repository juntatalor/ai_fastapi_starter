"""Глобальные фикстуры: async DB session + httpx AsyncClient + helpers.

Архитектура (session-scope):
* env выставляется через session-scope autouse fixture (:func:`_env_setup`),
  до первого импорта конфига. ``get_settings.cache_clear()`` вызывается
  после — чтобы pydantic-settings прочитал наши тестовые значения.
* Схема БД накатывается через ``alembic upgrade head`` — так тесты гоняют
  ту же цепочку миграций, что и прод. Downgrade → upgrade перед сессией,
  чтобы старт шёл на чистой БД.
* Один session-scope engine, базовый пул — коннекты переиспользуются
  между тестами (переоткрывать asyncpg-коннект на каждый тест дорого).

Изоляция (function-scope):
* ``db_session`` открывает транзакцию + SAVEPOINT; в конце теста
  ``ROLLBACK`` откатывает все изменения. Коннект возвращается в пул.
* ``client`` принимает ``db_session`` и подсовывает её в FastAPI через
  ``dependency_overrides[get_db]`` — тест и endpoint работают в одной
  транзакции, user_factory создаёт юзера, ручка этого юзера видит.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable, Iterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, create_async_engine

# Env-переменные ставим на модуль-уровне — до импорта src.config, т.к. alembic
# env.py вызывает get_settings() при первом импорте. session-scope autouse
# фикстура ниже страхует случай если что-то уже успело закешироваться.
_TEST_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@db:5432/app_test",
    "JWT_SECRET": "test-secret-32-chars-min-padding-aaa",
    "YANDEX_OAUTH_ENABLED": "false",
    "OPENAI_API_KEY": "test-fake",
    "S3_ENDPOINT_URL": "http://minio:9000",
    "S3_ACCESS_KEY_ID": "minioadmin",
    "S3_SECRET_ACCESS_KEY": "minioadmin",
    "S3_BUCKET_NAME": "app-test",
}
for _k, _v in _TEST_ENV.items():
    os.environ.setdefault(_k, _v)

from src.api.deps import get_db  # noqa: E402
from src.config import get_settings  # noqa: E402
from src.main import create_app  # noqa: E402
from src.models import *  # noqa: E402,F403 — регистрирует все модели в Base.metadata
from src.models.user import User, UserRole  # noqa: E402
from src.services.auth import hash_password, issue_token  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _env_setup() -> Iterator[None]:
    """Гарантируем что _TEST_ENV применён и Settings прочитают именно эти значения.

    ``get_settings`` кеширует Settings через lru_cache — если что-то
    закешировалось на старом env (например при импорте conftest.py
    другим раннером), сбрасываем кеш.
    """
    monkey = pytest.MonkeyPatch()
    for k, v in _TEST_ENV.items():
        monkey.setenv(k, v)
    get_settings.cache_clear()
    try:
        yield
    finally:
        monkey.undo()


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations(_env_setup: None) -> Iterator[None]:
    """Раскатываем схему через alembic ровно один раз на прогон.

    downgrade base → upgrade head — старт на чистой БД, даже если
    предыдущий прогон свалился и оставил мусор.

    Фикстура sync — alembic env.py при импорте зовёт ``asyncio.run(...)``,
    из async-контекста звать нельзя (``asyncio.run() cannot be called
    from a running event loop``).

    alembic.ini содержит [loggers] секцию, ``fileConfig`` внутри env.py
    перекручивает root logger на WARN → caplog в тестах ловит пустоту.
    Уровень root logger и флаг disabled восстанавливаем ниже.
    """
    import logging

    from alembic import command
    from alembic.config import Config

    root_before = logging.getLogger().level

    cfg = Config("alembic.ini")
    # alembic env.py читает settings при импорте (см. migrations/env.py) —
    # env к этому моменту уже выставлен через _env_setup.
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    # fileConfig в alembic env.py включает disable_existing_loggers=True —
    # ставит disabled=True на всех уже импортированных src.* логгерах,
    # из-за чего pytest caplog в тестах ловит пустоту. Раздавливаем обратно.
    for name in list(logging.root.manager.loggerDict):
        lg = logging.getLogger(name)
        lg.disabled = False
    logging.getLogger().setLevel(root_before)
    yield


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Один engine на всю сессию, дефолтный пул.

    asyncpg-коннекты переиспользуются между тестами — открытие коннекта
    дорогое (TLS handshake + auth). Изоляция тестов держится не на
    свежем коннекте, но через rollback транзакции в :func:`db_session`.
    """
    engine = create_async_engine(get_settings().database_url, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def _db_connection(db_engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    """Коннект + внешняя транзакция, откатывается по завершении теста.

    Приём «join-transaction»: session привязана к connection, session.commit
    коммитит вложенный SAVEPOINT (не внешний), внешний ROLLBACK в конце
    теста откатывает всё что тест написал — таблицы остаются чистыми.
    """
    async with db_engine.connect() as conn:
        trans = await conn.begin()
        try:
            yield conn
        finally:
            await trans.rollback()


@pytest_asyncio.fixture
async def db_session(_db_connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    """Сессия внутри внешней транзакции. session.commit → SAVEPOINT, не PG-commit."""
    session = AsyncSession(
        bind=_db_connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTP client, ``get_db`` возвращает ту же сессию что и тест.

    Клиент и ``user_factory`` видят одну транзакцию — юзер, созданный
    фабрикой до вызова эндпоинта, для эндпоинта уже существует.
    """
    app = create_app()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def user_factory(db_session: AsyncSession) -> Callable:
    """Фабрика юзеров. Использует ту же db_session что и client."""

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
