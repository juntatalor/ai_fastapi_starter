# ai_fastapi_starter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Готовый to-clone backend-стартер (FastAPI + worker + DB + S3 + LLM-tracking + JWT/Yandex auth + admin UI + light/dark) для запуска похожих на hrai проектов за полчаса.

**Architecture:** Backend (Python 3.14, FastAPI, SQLAlchemy async, pgqueuer, PG18) + Frontend (Vite+React+TS+Tailwind с dark mode) + Deploy (docker-compose для dev, Kubernetes/Kustomize для Timeweb). Auth = JWT+bcrypt + опциональный Yandex OAuth, флаг `YANDEX_OAUTH_ENABLED` гасит и backend-endpoints (404), и frontend-кнопку.

**Tech Stack:** Python 3.14 / FastAPI / SQLAlchemy 2.x async / asyncpg / PG 18 / Alembic / pgqueuer 1.0 / aiobotocore / openai SDK / Pydantic v2 / prometheus-client / pytest-asyncio / Vite 5 / React 18 / TypeScript / Tailwind 3 / React Router 6 / TanStack Query 5 / Axios.

**Reference:** `docs/specs/2026-06-19-ai-fastapi-starter-design.md`.

**Workflow:** Делать каждый chunk отдельной веткой → PR в `main` после моего ревью. Локально тесты в Docker: `docker compose run --rm test pytest`. Каждый chunk самодостаточен — после его merge стартер шагает к следующему этапу.

**Reference for copy-paste:** многие helpers портируем из hrai (`/home/juntatalor/projects/hrai`). В шагах указано «портировать из `<path>`» — это значит скопировать с минимальной адаптацией (убрать company-зависимости, оставить generic).

---

## Chunk A — Foundation (repo skeleton)

**Цель:** пустой репозиторий → каркас с pyproject, docker-окружением, базовыми конфигами. На этом этапе ничего не запускается, но `git clone && docker compose up db` уже работает.

### Task A.1 — pyproject.toml + структура пакетов

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`
- Create: `src/common/__init__.py`
- Create: `src/api/__init__.py`
- Create: `src/api/routes/__init__.py`
- Create: `src/api/routes/v1/__init__.py`
- Create: `src/db/__init__.py`
- Create: `src/models/__init__.py`
- Create: `src/schemas/__init__.py`
- Create: `src/services/__init__.py`
- Create: `src/workers/__init__.py`
- Create: `src/workers/worker/__init__.py`
- Create: `src/workers/worker/tasks/__init__.py`
- Create: `tests/__init__.py`, `tests/api/__init__.py`, `tests/workers/__init__.py`
- Create: `.python-version` → `3.14`

- [ ] **Step 1: pyproject.toml**

```toml
[project]
name = "ai_fastapi_starter"
version = "0.1.0"
description = "Backend starter (FastAPI + worker + DB + S3 + LLM) for AI projects"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.9",
    "pydantic-settings>=2.5",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "pgqueuer>=1.0",
    "aiobotocore>=2.13",
    "httpx>=0.27",
    "openai>=1.40",
    "bcrypt>=4.2",
    "PyJWT>=2.9",
    "prometheus-client>=0.20",
    "prometheus-fastapi-instrumentator>=7.0",
    "python-multipart>=0.0.9",
    "PyYAML>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "httpx>=0.27",
    "ruff>=0.6",
    "mypy>=1.11",
    "pre-commit>=3.8",
    "types-PyYAML",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "--strict-markers -ra --cov=src --cov-report=term-missing"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

[tool.mypy]
python_version = "3.14"
strict = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["pgqueuer.*", "aiobotocore.*"]
ignore_missing_imports = true
```

- [ ] **Step 2: создать все `__init__.py` (пустые)**

- [ ] **Step 3: .python-version + .gitignore**

`.python-version`:
```
3.14
```

`.gitignore` — стандартный Python + IDE + Docker + Node:
```
__pycache__/
*.py[cod]
.venv/
.env
.env.local
.coverage
htmlcov/
.pytest_cache/
.ruff_cache/
.mypy_cache/
dist/
build/
*.egg-info/
.DS_Store
.idea/
.vscode/
node_modules/
frontend/dist/
.pgqueuer.lock
test-results/
.claude/
docs/superpowers/
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: pyproject + package skeleton"
```

### Task A.2 — .env.example + .pre-commit-config.yaml

**Files:**
- Create: `.env.example`
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: `.env.example`** — все env-vars с подсказками:

```bash
# === App ===
APP_NAME=ai_fastapi_starter
DEBUG=false
APP_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO

# === Database ===
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app

# === JWT ===
JWT_SECRET=change-me-in-prod-please-32-chars-min
JWT_TTL_DAYS=7

# === Yandex OAuth (опционально, отключается одним флагом) ===
YANDEX_OAUTH_ENABLED=false
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
YANDEX_REDIRECT_URI=http://localhost:5173/oauth/yandex

# === OpenAI / LLM ===
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OPENAI_CHAT_TIMEOUT_SECONDS=60

# === S3 ===
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=app
S3_REGION=us-east-1

# === Worker ===
WORKER_METRICS_PORT=8001
PGQUEUER_DSN=postgresql://postgres:postgres@localhost:5432/app

# === Seed admin (scripts/seed_admin.py) ===
SEED_ADMIN_EMAIL=admin@example.com
SEED_ADMIN_PASSWORD=admin
```

- [ ] **Step 2: `.pre-commit-config.yaml`**:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, types-PyYAML]
        exclude: "^(tests/|migrations/|frontend/)"
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "chore: .env.example + pre-commit config"
```

### Task A.3 — Dockerfile.app + Dockerfile.migrate + Dockerfile.worker + Dockerfile.test

**Files:** `docker/Dockerfile.app`, `docker/Dockerfile.migrate`, `docker/Dockerfile.worker`, `docker/Dockerfile.test`.

Все 4 используют uv + python:3.14-slim base. Минимально:

- [ ] **Step 1: `docker/Dockerfile.app`**

```dockerfile
FROM python:3.14-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv
COPY pyproject.toml /app/
RUN uv sync --no-dev --no-install-project
COPY src /app/src
COPY scripts /app/scripts
EXPOSE 8000
ENV PYTHONPATH=/app
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: `docker/Dockerfile.worker`** — copy с `app`, но `CMD` другой:

```dockerfile
# идентично Dockerfile.app кроме CMD
CMD ["uv", "run", "python", "-m", "src.workers.worker.main"]
```

- [ ] **Step 3: `docker/Dockerfile.migrate`** — slim, только alembic + pgqueuer install:

```dockerfile
FROM python:3.14-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv
COPY pyproject.toml /app/
RUN uv sync --no-dev --no-install-project --no-group dev \
    --extra-package "alembic" --extra-package "asyncpg" --extra-package "pgqueuer"
COPY migrations /app/migrations
COPY alembic.ini /app/
COPY src/db /app/src/db
COPY src/models /app/src/models
COPY scripts/migrate.sh /app/scripts/migrate.sh
RUN chmod +x /app/scripts/migrate.sh
ENV PYTHONPATH=/app
CMD ["/app/scripts/migrate.sh"]
```

- [ ] **Step 4: `docker/Dockerfile.test`** — full + dev-зависимости:

```dockerfile
FROM python:3.14-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv
COPY pyproject.toml /app/
RUN uv sync --no-install-project
COPY . /app/
ENV PYTHONPATH=/app
CMD ["uv", "run", "pytest"]
```

- [ ] **Step 5: `scripts/migrate.sh`**:

```bash
#!/bin/sh
set -e
echo "Running alembic migrations..."
uv run alembic upgrade head
echo "Installing pgqueuer schema..."
uv run pgq install --dsn "$PGQUEUER_DSN" || true
echo "Migrate job finished."
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "chore: Dockerfiles for app/worker/migrate/test"
```

### Task A.4 — docker-compose.yml

**Files:** `docker-compose.yml`

- [ ] **Step 1:**

```yaml
services:
  db:
    image: postgres:18-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./docker/initdb.sh:/docker-entrypoint-initdb.d/initdb.sh:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10

  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  migrate:
    build:
      context: .
      dockerfile: docker/Dockerfile.migrate
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/app
      PGQUEUER_DSN: postgresql://postgres:postgres@db:5432/app
    depends_on:
      db:
        condition: service_healthy

  app:
    build:
      context: .
      dockerfile: docker/Dockerfile.app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
      - JWT_SECRET=${JWT_SECRET:-dev-secret-change-me-32-chars-please}
      - YANDEX_OAUTH_ENABLED=${YANDEX_OAUTH_ENABLED:-false}
      - YANDEX_CLIENT_ID=${YANDEX_CLIENT_ID:-}
      - YANDEX_CLIENT_SECRET=${YANDEX_CLIENT_SECRET:-}
      - YANDEX_REDIRECT_URI=${YANDEX_REDIRECT_URI:-http://localhost:5173/oauth/yandex}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://api.openai.com/v1}
      - OPENAI_DEFAULT_MODEL=${OPENAI_DEFAULT_MODEL:-gpt-4o-mini}
      - S3_ENDPOINT_URL=http://minio:9000
      - S3_ACCESS_KEY_ID=minioadmin
      - S3_SECRET_ACCESS_KEY=minioadmin
      - S3_BUCKET_NAME=app
      - S3_REGION=us-east-1
    depends_on:
      db:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    volumes:
      - ./src:/app/src

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
      - PGQUEUER_DSN=postgresql://postgres:postgres@db:5432/app
      - WORKER_METRICS_PORT=8001
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://api.openai.com/v1}
      - OPENAI_DEFAULT_MODEL=${OPENAI_DEFAULT_MODEL:-gpt-4o-mini}
    depends_on:
      db:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    volumes:
      - ./src:/app/src

  test:
    build:
      context: .
      dockerfile: docker/Dockerfile.test
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app_test
      - JWT_SECRET=test-secret-32-chars-min-padding-aaa
      - YANDEX_OAUTH_ENABLED=false
      - OPENAI_API_KEY=test-fake-key
      - S3_ENDPOINT_URL=http://minio:9000
      - S3_ACCESS_KEY_ID=minioadmin
      - S3_SECRET_ACCESS_KEY=minioadmin
      - S3_BUCKET_NAME=app-test
    depends_on:
      db:
        condition: service_healthy
      minio:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
    ports:
      - "5173:80"
    depends_on:
      - app

volumes:
  db_data:
  minio_data:
```

- [ ] **Step 2: `docker/initdb.sh`** — создание тестовой БД:

```bash
#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE app_test;
EOSQL
```

- [ ] **Step 3: smoke** — `docker compose up db -d` запускается → `docker compose down`.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "chore: docker-compose + initdb"
```

---

## Chunk B — DB foundation + models

### Task B.1 — async engine, Base, session

**Files:**
- Create: `src/db/session.py`

- [ ] **Step 1:**

```python
"""Async SQLAlchemy engine + sessionmaker + declarative Base."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import get_settings


class Base(DeclarativeBase):
    """Базовый класс ORM-моделей. Все модели наследуют его."""


_settings = get_settings()
engine = create_async_engine(
    _settings.database_url,
    echo=_settings.debug,
    pool_pre_ping=True,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Контекстный менеджер с авто-rollback на исключении."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 2: Commit** → `git add src/db/session.py && git commit -m "feat(db): async engine + session"`

### Task B.2 — Settings (config.py)

**Files:**
- Create: `src/config.py`

- [ ] **Step 1:**

```python
"""AppSettings — env-driven config (Pydantic v2)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Конфиг FastAPI-приложения. Читается из env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="ai_fastapi_starter", description="Имя сервиса для логов и UI.")
    debug: bool = Field(default=False, description="SQL-echo, verbose-логи.")
    app_base_url: str = Field(
        default="http://localhost:8000",
        description="Public URL приложения (для OAuth redirect и т. п.).",
    )
    log_level: str = Field(default="INFO", description="Уровень логирования.")

    database_url: str = Field(description="postgresql+asyncpg DSN.")

    jwt_secret: str = Field(min_length=32, description="HMAC ключ для JWT.")
    jwt_ttl_days: int = Field(default=7, ge=1, le=90, description="Срок жизни access token.")

    yandex_oauth_enabled: bool = Field(default=False, description="Kill-switch Yandex OAuth.")
    yandex_client_id: str = Field(default="", description="ClientID из ya.console.")
    yandex_client_secret: str = Field(default="", description="ClientSecret.")
    yandex_redirect_uri: str = Field(
        default="http://localhost:5173/oauth/yandex",
        description="Куда Yandex возвращает code (frontend route).",
    )

    openai_api_key: str = Field(default="", description="OpenAI / compat API key.")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL для OpenAI-совместимого провайдера.",
    )
    openai_default_model: str = Field(default="gpt-4o-mini", description="Дефолт LLM-модели.")
    openai_chat_timeout_seconds: float = Field(default=60.0, ge=1.0, le=600.0)

    s3_endpoint_url: str = Field(default="http://localhost:9000")
    s3_access_key_id: str = Field(default="")
    s3_secret_access_key: str = Field(default="")
    s3_bucket_name: str = Field(default="app")
    s3_region: str = Field(default="us-east-1")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()  # type: ignore[call-arg]
```

- [ ] **Step 2: failing test** `tests/test_config.py`:

```python
from src.config import AppSettings


def test_settings_load_with_minimal_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:y@z/db")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    s = AppSettings(_env_file=None)  # type: ignore[call-arg]
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.jwt_ttl_days == 7
    assert s.yandex_oauth_enabled is False
```

Run → PASS.

- [ ] **Step 3: Commit** `feat(config): AppSettings + env mapping`

### Task B.3 — Alembic init

**Files:**
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`
- Create: `migrations/versions/__init__.py`

- [ ] **Step 1: `alembic.ini`** (минимум):

```ini
[alembic]
script_location = migrations
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(rev)s_%%(slug)s
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: `migrations/env.py`** — async-aware, читает DATABASE_URL:

```python
"""Alembic async env — autogenerate использует src.models metadata."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.config import get_settings
from src.db.session import Base
from src.models import *  # noqa: F401,F403 — регистрирует модели

config = context.config

# Подставляем DSN из настроек (sync-вариант для alembic).
settings = get_settings()
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("+asyncpg", ""),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=settings.database_url,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


run_migrations_online()
```

- [ ] **Step 3: `migrations/script.py.mako`** — стандартный шаблон Alembic.

- [ ] **Step 4: Commit** `chore(db): alembic init`

### Task B.4 — User model + миграция

**Files:**
- Create: `src/models/__init__.py` (импортирует User и UsageLog)
- Create: `src/models/user.py`
- Create: `migrations/versions/2026_06_19_<rev>_initial.py`

- [ ] **Step 1: `src/models/user.py`**:

```python
"""ORM-модель User — без company-привязок."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class UserRole(StrEnum):
    """Ролевая модель: user + admin. Расширять — в проекте."""

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """Пользователь системы. Login по email."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(120), nullable=True)
    yandex_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        String(16), nullable=False, default=UserRole.USER, server_default=UserRole.USER.value
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 2: `src/models/__init__.py`**:

```python
"""Реэкспорт ORM-моделей. Импорт через `from src.models import *` в alembic env."""

from src.models.user import User, UserRole
from src.models.usage_log import UsageLog  # noqa: F401  — модель из B.5

__all__ = ["User", "UserRole", "UsageLog"]
```

(`usage_log` создаётся в B.5; на этом этапе импорт упадёт — закладываем,
сначала создадим B.5, потом запустим миграцию.)

- [ ] **Step 3: см. Task B.5** перед миграцией.

### Task B.5 — UsageLog model

**Files:** Create `src/models/usage_log.py`

- [ ] **Step 1:**

```python
"""Лог токенов LLM-вызовов. Используется TrackedOpenAI."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class UsageLog(Base):
    """Один LLM-вызов: модель, токены, кто инициировал, когда."""

    __tablename__ = "usage_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    operation: Mapped[str] = mapped_column(String(64), nullable=False, default="chat")
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 2: Сгенерировать миграцию**:

```bash
docker compose run --rm migrate uv run alembic revision --autogenerate -m "initial users + usage_log"
```

Получим файл `migrations/versions/2026_06_19_<rev>_initial_users_usage_log.py`. Verify содержимое (create_table users + usage_log).

- [ ] **Step 3: Применить миграцию**:

```bash
docker compose up migrate
```

- [ ] **Step 4: Smoke test** — `tests/test_db.py`:

```python
import pytest
from sqlalchemy import text

from src.db.session import async_session_maker


@pytest.mark.asyncio
async def test_users_table_exists():
    async with async_session_maker() as s:
        row = await s.execute(text("SELECT 1 FROM users LIMIT 1"))
        assert row is not None
```

- [ ] **Step 5: Commit** `feat(db): User + UsageLog models + initial migration`

---

## Chunk C — Common helpers

### Task C.1 — logging_config

**Files:** `src/common/logging_config.py`

- [ ] **Step 1:** Портировать из `hrai/src/common/logging_config.py`. Структура:

```python
"""JSON-логгер с correlation через ContextVar."""

import json
import logging
from datetime import UTC, datetime

from src.context import current_operation


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(timespec="seconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        op = current_operation.get(None)
        if op:
            payload["op"] = op
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logging_config(level: str = "INFO") -> dict[str, object]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "json"},
        },
        "root": {"handlers": ["console"], "level": level},
    }
```

- [ ] **Step 2: `src/context.py`**:

```python
"""ContextVars для correlation между логами и операциями."""

from contextvars import ContextVar

current_operation: ContextVar[str | None] = ContextVar("current_operation", default=None)
```

- [ ] **Step 3: Commit** `feat(common): logging + context vars`

### Task C.2 — exceptions

**Files:** `src/common/exceptions.py`

```python
"""Базовые исключения проекта."""


class AppError(Exception):
    """Базовый класс для всех бизнес-исключений."""


class NotFoundError(AppError):
    """Ресурс не найден."""


class PermissionDeniedError(AppError):
    """Доступ запрещён."""


class ConflictError(AppError):
    """Состояние ресурса не позволяет операцию."""


class ExternalServiceError(AppError):
    """Внешний сервис (LLM, S3, OAuth) недоступен."""
```

Commit.

### Task C.3 — retry helper

`src/common/retry.py` — портируем из hrai `src/common/retry.py` (exponential backoff + jitter). Commit.

### Task C.4 — TrackedOpenAI

**Files:** `src/common/openai_client.py`

- [ ] **Step 1:** wrapper:

```python
"""TrackedOpenAI — AsyncOpenAI с логированием usage в БД."""

from collections.abc import Callable
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.models.usage_log import UsageLog


class TrackedOpenAI:
    """Тонкая обёртка вокруг AsyncOpenAI с записью usage в usage_log."""

    def __init__(
        self,
        client: AsyncOpenAI,
        *,
        session_factory: async_sessionmaker,
        default_model: str,
    ) -> None:
        self._client = client
        self._session_factory = session_factory
        self._default_model = default_model

    @property
    def chat(self) -> "ChatNamespace":
        return ChatNamespace(self)

    async def _log_usage(
        self,
        *,
        user_id: int | None,
        operation: str,
        model: str,
        usage: Any,
    ) -> None:
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        completion = getattr(usage, "completion_tokens", 0) or 0
        total = getattr(usage, "total_tokens", prompt + completion) or 0
        async with self._session_factory() as session:
            session.add(
                UsageLog(
                    user_id=user_id,
                    operation=operation,
                    model=model,
                    prompt_tokens=prompt,
                    completion_tokens=completion,
                    total_tokens=total,
                )
            )
            await session.commit()


class ChatNamespace:
    def __init__(self, parent: TrackedOpenAI) -> None:
        self._parent = parent

    async def create(
        self,
        *,
        messages: list[dict[str, Any]],
        user_id: int | None = None,
        operation: str = "chat",
        model: str | None = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        chosen = model or self._parent._default_model
        resp = await self._parent._client.chat.completions.create(
            model=chosen, messages=messages, **kwargs
        )
        if resp.usage:
            await self._parent._log_usage(
                user_id=user_id, operation=operation, model=chosen, usage=resp.usage
            )
        return resp


def create_tracked_openai(
    *, settings, session_factory: async_sessionmaker
) -> TrackedOpenAI:
    raw = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    return TrackedOpenAI(
        raw, session_factory=session_factory, default_model=settings.openai_default_model
    )
```

- [ ] **Step 2: Test** `tests/common/test_openai_tracking.py` — мок AsyncOpenAI, проверка что после `chat.create` появляется запись в usage_log.

- [ ] **Step 3: Commit** `feat(common): TrackedOpenAI with usage logging`

### Task C.5 — S3 client

**Files:** `src/common/s3/__init__.py`, `src/common/s3/client.py`

- [ ] **Step 1:** aiobotocore-based helper:

```python
"""S3 client — async через aiobotocore. Endpoint совместим с MinIO/Twcstorage."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from aiobotocore.session import get_session

from src.config import get_settings


@asynccontextmanager
async def s3_client() -> AsyncIterator:
    s = get_settings()
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        aws_access_key_id=s.s3_access_key_id,
        aws_secret_access_key=s.s3_secret_access_key,
        region_name=s.s3_region,
    ) as client:
        yield client


async def upload_bytes(*, key: str, data: bytes, content_type: str | None = None) -> None:
    s = get_settings()
    async with s3_client() as client:
        kwargs: dict = {"Bucket": s.s3_bucket_name, "Key": key, "Body": data}
        if content_type:
            kwargs["ContentType"] = content_type
        await client.put_object(**kwargs)


async def download_bytes(key: str) -> bytes:
    s = get_settings()
    async with s3_client() as client:
        resp = await client.get_object(Bucket=s.s3_bucket_name, Key=key)
        async with resp["Body"] as body:
            return await body.read()


async def presigned_get_url(key: str, expires_in: int = 3600) -> str:
    s = get_settings()
    async with s3_client() as client:
        return await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": s.s3_bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )


async def delete_object(key: str) -> None:
    s = get_settings()
    async with s3_client() as client:
        await client.delete_object(Bucket=s.s3_bucket_name, Key=key)
```

- [ ] **Step 2: Commit** `feat(common): S3 client (aiobotocore)`

### Task C.6 — Queue (pgqueuer adapter)

**Files:** `src/common/queue/__init__.py`, `src/common/queue/base.py`, `src/common/queue/pgqueuer.py`

- [ ] **Step 1:** Портировать из hrai `src/common/queue/*` (AbstractQueue, PgQueuer-обёртка). Минимальная адаптация — убрать hrai-specific код.

```python
# src/common/queue/base.py
from abc import ABC, abstractmethod
from collections.abc import Callable


class AbstractQueue(ABC):
    """Абстракция over pgqueuer для тестируемости."""

    @abstractmethod
    async def enqueue(self, entrypoint: str, payload: bytes) -> None: ...
    @abstractmethod
    def register_handler(self, entrypoint: str, handler: Callable) -> None: ...
    @abstractmethod
    async def run(self) -> None: ...
    @abstractmethod
    async def stop(self) -> None: ...
```

```python
# src/common/queue/pgqueuer.py
from collections.abc import Callable

import asyncpg
from pgqueuer import PgQueuer
from pgqueuer.db import AsyncpgDriver

from src.common.queue.base import AbstractQueue


class PgQueue(AbstractQueue):
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._driver: AsyncpgDriver | None = None
        self._pgq: PgQueuer | None = None
        self._handlers: dict[str, Callable] = {}

    async def _ensure(self) -> PgQueuer:
        if self._pgq is None:
            pool = await asyncpg.create_pool(self._dsn)
            self._driver = AsyncpgDriver(pool)
            self._pgq = PgQueuer(self._driver)
            for name, fn in self._handlers.items():
                self._pgq.entrypoint(name)(fn)
        return self._pgq

    async def enqueue(self, entrypoint: str, payload: bytes) -> None:
        pgq = await self._ensure()
        await pgq.queries.enqueue([entrypoint], [payload], [0])

    def register_handler(self, entrypoint: str, handler: Callable) -> None:
        self._handlers[entrypoint] = handler

    async def run(self) -> None:
        pgq = await self._ensure()
        await pgq.run()

    async def stop(self) -> None:
        if self._pgq:
            await self._pgq.shutdown()
```

```python
# src/common/queue/__init__.py
from src.common.queue.base import AbstractQueue
from src.common.queue.pgqueuer import PgQueue


def create_queue(dsn: str) -> AbstractQueue:
    return PgQueue(dsn)


__all__ = ["AbstractQueue", "PgQueue", "create_queue"]
```

- [ ] **Step 2: Commit** `feat(common): pgqueuer adapter`

---

## Chunk D — Auth (JWT + password)

### Task D.1 — Schemas

**Files:** `src/schemas/auth.py`

```python
"""Pydantic-схемы auth-роутов."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole


class LoginRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    email: EmailStr = Field(description="Email пользователя.")
    password: str = Field(min_length=1, description="Пароль в открытом виде (по HTTPS).")


class TokenResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    has_password: bool = Field(description="Можно ли логиниться по password.")
    has_yandex: bool = Field(description="Привязан ли Yandex-аккаунт.")


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    current_password: str | None = Field(
        default=None,
        description="Текущий пароль. Обязателен если у user'а уже есть password_hash.",
    )
    new_password: str = Field(min_length=8, max_length=128, description="Новый пароль ≥8 символов.")
```

Commit `feat(auth): pydantic schemas`.

### Task D.2 — services/auth.py (bcrypt + JWT)

**Files:** `src/services/auth.py`

```python
"""Auth-сервис: bcrypt + JWT. Никаких company-привязок."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import NotFoundError, PermissionDeniedError
from src.config import get_settings
from src.models.user import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def issue_token(user_id: int) -> str:
    s = get_settings()
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(days=s.jwt_ttl_days),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> int:
    s = get_settings()
    data = jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    return int(data["sub"])


async def authenticate(db: AsyncSession, *, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise NotFoundError("Неверный email или пароль")
    if user.password_hash is None:
        raise PermissionDeniedError("Войдите через Yandex или попросите admin'а сбросить пароль.")
    if not verify_password(password, user.password_hash):
        raise NotFoundError("Неверный email или пароль")
    return user


async def get_user(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("user")
    return user


async def change_password(
    db: AsyncSession, *, user: User, current_password: str | None, new_password: str
) -> None:
    if user.password_hash is not None:
        if current_password is None or not verify_password(current_password, user.password_hash):
            raise PermissionDeniedError("Текущий пароль неверен")
    user.password_hash = hash_password(new_password)
    await db.commit()
```

Tests `tests/services/test_auth.py` — hash/verify, issue/decode, authenticate happy + wrong password.
Commit `feat(auth): bcrypt + JWT service`.

### Task D.3 — deps + /login + /me + /password

**Files:**
- Create: `src/api/deps.py`
- Create: `src/api/routes/v1/auth.py`

`deps.py`:

```python
"""FastAPI dependencies: get_db, get_current_user, get_current_admin."""

from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import NotFoundError
from src.db.session import async_session_maker
from src.models.user import User, UserRole
from src.services.auth import decode_token, get_user

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token")
    try:
        user_id = decode_token(creds.credentials)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    try:
        return await get_user(db, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found") from e


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
```

`routes/v1/auth.py`:

```python
"""Auth routes: /login, /me, /password, и (опционально) Yandex."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.common.exceptions import NotFoundError, PermissionDeniedError
from src.models.user import User
from src.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserOut
from src.services.auth import authenticate, change_password, issue_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        user = await authenticate(db, email=body.email, password=body.password)
    except (NotFoundError, PermissionDeniedError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    return TokenResponse(access_token=issue_token(user.id))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(
        {
            **user.__dict__,
            "has_password": user.password_hash is not None,
            "has_yandex": user.yandex_id is not None,
        }
    )


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await change_password(
            db,
            user=user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
```

Tests `tests/api/test_auth.py` — login happy, login wrong password, me with token, password change happy + wrong current.

Commit `feat(api): /login /me /password`.

---

## Chunk E — Yandex OAuth (флаг-гейтинг)

### Task E.1 — services/yandex_oauth.py

**Files:** `src/services/yandex_oauth.py`

```python
"""Yandex OAuth — code → email + yandex_id + display_name."""

from dataclasses import dataclass

import httpx

from src.common.exceptions import ExternalServiceError
from src.config import get_settings


@dataclass(frozen=True)
class YandexUserInfo:
    yandex_id: str
    email: str
    display_name: str | None


async def authorize_url() -> str:
    s = get_settings()
    return (
        "https://oauth.yandex.ru/authorize?response_type=code"
        f"&client_id={s.yandex_client_id}&redirect_uri={s.yandex_redirect_uri}"
    )


async def exchange_code(code: str) -> YandexUserInfo:
    s = get_settings()
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": s.yandex_client_id,
                "client_secret": s.yandex_client_secret,
            },
        )
        if token_resp.status_code != 200:
            raise ExternalServiceError(f"yandex token: {token_resp.text}")
        access_token = token_resp.json()["access_token"]

        user_resp = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {access_token}"},
            params={"format": "json"},
        )
        if user_resp.status_code != 200:
            raise ExternalServiceError(f"yandex user info: {user_resp.text}")
        data = user_resp.json()
        return YandexUserInfo(
            yandex_id=str(data["id"]),
            email=data.get("default_email") or "",
            display_name=data.get("real_name") or data.get("display_name"),
        )
```

Tests с моком httpx.

Commit `feat(auth): yandex oauth service`.

### Task E.2 — /yandex/start + /yandex/callback (флаг → 404)

Дописать в `src/api/routes/v1/auth.py`:

```python
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from src.config import get_settings
from src.models.user import User
from src.services.yandex_oauth import authorize_url, exchange_code


def _ensure_yandex_enabled() -> None:
    if not get_settings().yandex_oauth_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/yandex/start")
async def yandex_start() -> RedirectResponse:
    _ensure_yandex_enabled()
    return RedirectResponse(await authorize_url(), status_code=302)


@router.get("/yandex/callback", response_model=TokenResponse)
async def yandex_callback(code: str, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    _ensure_yandex_enabled()
    info = await exchange_code(code)
    result = await db.execute(select(User).where(User.email == info.email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь не зарегистрирован. Попросите администратора добавить ваш email.",
        )
    if user.yandex_id != info.yandex_id:
        user.yandex_id = info.yandex_id
    if not user.full_name and info.display_name:
        user.full_name = info.display_name
    await db.commit()
    return TokenResponse(access_token=issue_token(user.id))
```

Tests:
- `tests/api/test_yandex.py::test_disabled_returns_404` — флаг false → /yandex/start 404
- `test_callback_links_existing_user` — мокаем `exchange_code`, юзер уже есть → token
- `test_callback_unknown_email_403` — юзера нет → 403

Commit `feat(auth): yandex /start /callback + флаг 404`.

---

## Chunk F — Admin API (users CRUD)

### Task F.1 — Schemas

**Files:** `src/schemas/admin.py`

```python
"""Admin-схемы для /admin/users."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    has_password: bool
    has_yandex: bool


class AdminUserCreate(BaseModel):
    model_config = ConfigDict(frozen=True)
    email: EmailStr
    full_name: str | None = None
    role: UserRole = UserRole.USER
    password: str | None = Field(
        default=None, min_length=8, description="Опционально — если не задан, юзер войдёт через Yandex."
    )


class AdminUserUpdate(BaseModel):
    model_config = ConfigDict(frozen=True)
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class AdminResetPassword(BaseModel):
    model_config = ConfigDict(frozen=True)
    new_password: str = Field(min_length=8, max_length=128)
```

### Task F.2 — services/user.py

```python
"""User-сервис для admin-операций."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import ConflictError, NotFoundError
from src.models.user import User, UserRole
from src.services.auth import hash_password


async def list_users(db: AsyncSession, *, limit: int = 100) -> list[User]:
    result = await db.execute(select(User).order_by(User.id.desc()).limit(limit))
    return list(result.scalars())


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("user")
    return user


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    full_name: str | None,
    role: UserRole,
    password: str | None,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        role=role,
        password_hash=hash_password(password) if password else None,
        is_active=True,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise ConflictError(f"email {email} занят") from e
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    *,
    user: User,
    full_name: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> User:
    if full_name is not None:
        user.full_name = full_name
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    await db.commit()
    return user


async def reset_password(db: AsyncSession, *, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    await db.commit()


async def soft_delete(db: AsyncSession, *, user: User) -> None:
    user.is_active = False
    await db.commit()
```

Commit.

### Task F.3 — /admin/users routes

**Files:** `src/api/routes/v1/admin_users.py`

```python
"""CRUD /admin/users — только role=admin."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_admin, get_db
from src.common.exceptions import ConflictError, NotFoundError
from src.models.user import User
from src.schemas.admin import (
    AdminResetPassword,
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
)
from src.services.user import (
    create_user,
    get_user_by_id,
    list_users,
    reset_password,
    soft_delete,
    update_user,
)

router = APIRouter(prefix="/admin/users", tags=["admin"])


def _to_out(u: User) -> AdminUserOut:
    return AdminUserOut.model_validate(
        {
            **u.__dict__,
            "has_password": u.password_hash is not None,
            "has_yandex": u.yandex_id is not None,
        }
    )


@router.get("", response_model=list[AdminUserOut])
async def list_(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
) -> list[AdminUserOut]:
    users = await list_users(db, limit=limit)
    return [_to_out(u) for u in users]


@router.post("", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_(
    body: AdminUserCreate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    try:
        user = await create_user(
            db,
            email=body.email,
            full_name=body.full_name,
            role=body.role,
            password=body.password,
        )
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return _to_out(user)


@router.patch("/{user_id}", response_model=AdminUserOut)
async def update_(
    user_id: int,
    body: AdminUserUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    try:
        user = await get_user_by_id(db, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail="user") from e
    user = await update_user(
        db, user=user, full_name=body.full_name, role=body.role, is_active=body.is_active
    )
    return _to_out(user)


@router.post("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_(
    user_id: int,
    body: AdminResetPassword,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await get_user_by_id(db, user_id)
    await reset_password(db, user=user, new_password=body.new_password)
    return Response(status_code=204)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_(
    user_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await get_user_by_id(db, user_id)
    await soft_delete(db, user=user)
    return Response(status_code=204)
```

Tests `tests/api/test_admin_users.py` — list / create / update role / 409 на duplicate / reset password / soft delete + проверка что user без admin-роли получает 403.

Commit `feat(admin): users CRUD`.

---

## Chunk G — main.py + config endpoint + healthcheck + metrics

### Task G.1 — main.py + healthcheck + metrics + config endpoint

**Files:**
- Create: `src/main.py`
- Create: `src/api/routes/v1/healthcheck.py`
- Create: `src/api/routes/v1/config.py`

`config.py`:

```python
"""Публичный config endpoint — фронт читает на старте."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import get_settings

router = APIRouter(prefix="/config", tags=["config"])


class PublicConfig(BaseModel):
    app_name: str
    yandex_enabled: bool


@router.get("", response_model=PublicConfig)
def get_public_config() -> PublicConfig:
    s = get_settings()
    return PublicConfig(app_name=s.app_name, yandex_enabled=s.yandex_oauth_enabled)
```

`healthcheck.py`:

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
```

`src/main.py`:

```python
"""FastAPI entry-point."""

import logging
from contextlib import asynccontextmanager
from logging.config import dictConfig

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.routes.v1 import admin_users, auth, config as config_route, healthcheck
from src.common.logging_config import get_logging_config
from src.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    dictConfig(get_logging_config(get_settings().log_level))
    logging.getLogger(__name__).info("App started: %s", get_settings().app_name)
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=s.app_name, debug=s.debug, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    app.include_router(healthcheck.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(admin_users.router, prefix="/api/v1")
    app.include_router(config_route.router, prefix="/api/v1")
    return app


app = create_app()
```

Tests:
- `tests/api/test_healthcheck.py::test_returns_ok`
- `tests/api/test_config_endpoint.py::test_config_returns_yandex_flag` (true/false)
- `tests/api/test_app_boots.py::test_openapi_includes_admin_users`

Commit `feat(app): main + healthcheck + metrics + config endpoint`.

---

## Chunk H — Worker

### Task H.1 — Worker config + metrics

**Files:**
- Create: `src/workers/worker/config.py`
- Create: `src/workers/worker/metrics.py`

`config.py`:

```python
"""WorkerSettings — независимая от AppSettings конфигурация."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    pgqueuer_dsn: str
    worker_metrics_port: int = Field(default=8001, ge=1024, le=65535)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_default_model: str = "gpt-4o-mini"
    log_level: str = "INFO"


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()  # type: ignore[call-arg]
```

`metrics.py`:

```python
"""Prometheus-метрики worker'а."""

from prometheus_client import Counter, Gauge, Histogram

jobs_processed_total = Counter(
    "jobs_processed_total", "Total processed jobs", ["task", "status"]
)
job_duration_seconds = Histogram(
    "job_duration_seconds",
    "Time spent in handler",
    ["task"],
    buckets=(0.1, 0.5, 1.0, 5.0, 30.0, 60.0, 300.0),
)
worker_uptime_seconds = Gauge("worker_uptime_seconds", "Seconds since worker start")
```

Commit `feat(worker): config + metrics`.

### Task H.2 — Example task

**Files:** `src/workers/worker/tasks/example_task.py`

```python
"""Пример pgqueuer-handler. В реальном проекте таски кладутся рядом."""

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ExamplePayload(BaseModel):
    message: str


async def handle_example(payload: bytes) -> None:
    data = ExamplePayload.model_validate_json(payload)
    logger.info("example task: %s", data.message)
```

Commit.

### Task H.3 — Worker entrypoint

**Files:**
- Create: `src/workers/worker/app.py`
- Create: `src/workers/worker/main.py`

`app.py` — FastAPI(metrics+healthcheck) запускается в одном event-loop с pgqueuer'ом:

```python
"""Worker app — поднимает FastAPI (metrics) + pgqueuer.

FastAPI отвечает на /healthcheck и /metrics, pgqueuer крутит handler'ы.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from functools import partial
from logging.config import dictConfig

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.common.logging_config import get_logging_config
from src.common.queue import create_queue
from src.workers.worker.config import get_worker_settings
from src.workers.worker.metrics import (
    job_duration_seconds,
    jobs_processed_total,
    worker_uptime_seconds,
)
from src.workers.worker.tasks.example_task import handle_example

logger = logging.getLogger(__name__)


async def _wrap(task_name: str, handler, payload: bytes) -> None:
    t0 = time.monotonic()
    status = "success"
    try:
        await handler(payload)
    except Exception:
        status = "failure"
        logger.exception("%s failed", task_name)
        raise
    finally:
        jobs_processed_total.labels(task=task_name, status=status).inc()
        job_duration_seconds.labels(task=task_name).observe(time.monotonic() - t0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_worker_settings()
    dictConfig(get_logging_config(s.log_level))
    queue = create_queue(s.pgqueuer_dsn)
    queue.register_handler("example", partial(_wrap, "example", handle_example))
    started = time.monotonic()

    async def _uptime():
        while True:
            worker_uptime_seconds.set(time.monotonic() - started)
            await asyncio.sleep(5)

    uptime_task = asyncio.create_task(_uptime())
    queue_task = asyncio.create_task(queue.run())
    logger.info("Worker started")
    try:
        yield
    finally:
        uptime_task.cancel()
        await queue.stop()
        queue_task.cancel()


def create_app() -> FastAPI:
    app = FastAPI(title="worker", lifespan=lifespan)
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    @app.get("/healthcheck")
    def _hc() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

`main.py`:

```python
"""Worker CLI entry-point."""

import uvicorn

from src.workers.worker.config import get_worker_settings


def main() -> None:
    s = get_worker_settings()
    uvicorn.run(
        "src.workers.worker.app:app",
        host="0.0.0.0",
        port=s.worker_metrics_port,
        log_level=s.log_level.lower(),
    )


if __name__ == "__main__":
    main()
```

Test `tests/workers/test_example_task.py` — `handle_example(b'{"message":"hi"}')` не падает и пишет в лог.

Commit `feat(worker): pgqueuer + metrics + example task`.

---

## Chunk I — Tests skeleton

### Task I.1 — conftest

**Files:** `tests/conftest.py`

```python
"""Глобальные фикстуры: async db_session + httpx AsyncClient."""

import asyncio
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import async_session_maker, engine
from src.main import create_app
from src.models.user import User, UserRole
from src.services.auth import hash_password, issue_token


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Savepoint-based session — каждый тест в своей транзакции."""
    async with engine.connect() as conn:
        trans = await conn.begin()
        async_factory = async_session_maker.configure(bind=conn)
        async with async_session_maker() as s:
            yield s
        await trans.rollback()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def user_factory(db_session):
    async def _make(*, email: str, role: UserRole = UserRole.USER, password: str = "Password1!"):
        u = User(
            email=email,
            full_name=email.split("@")[0],
            role=role,
            password_hash=hash_password(password),
            is_active=True,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        return u

    return _make


@pytest.fixture
def auth_headers():
    def _make(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {issue_token(user.id)}"}

    return _make
```

Commit `test: conftest`.

### Task I.2 — Прогон полного suite в Docker

- [ ] `docker compose run --rm test pytest` — все тесты passed, coverage ≥80% для `src/services` и `src/common`.

Commit `test: full suite green`.

---

## Chunk J — Frontend foundation

### Task J.1 — Vite + TS + Tailwind init

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles/index.css`

- [ ] **Step 1: `package.json`**:

```json
{
  "name": "ai_fastapi_starter_frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.59.0",
    "axios": "^1.7.7",
    "lucide-react": "^0.450.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.27.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.11",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.2",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.13",
    "typescript": "^5.6.3",
    "vite": "^5.4.10"
  }
}
```

- [ ] **Step 2: `tailwind.config.ts`**:

```ts
import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--color-bg) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        text: "rgb(var(--color-text) / <alpha-value>)",
        muted: "rgb(var(--color-text-muted) / <alpha-value>)",
        primary: "rgb(var(--color-primary) / <alpha-value>)",
        border: "rgb(var(--color-border) / <alpha-value>)",
      },
    },
  },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 3: `src/styles/index.css`**:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --color-bg: 255 255 255;
    --color-surface: 248 250 252;
    --color-text: 15 23 42;
    --color-text-muted: 100 116 139;
    --color-primary: 99 102 241;
    --color-border: 226 232 240;
  }
  .dark {
    --color-bg: 15 23 42;
    --color-surface: 30 41 59;
    --color-text: 226 232 240;
    --color-text-muted: 148 163 184;
    --color-primary: 129 140 248;
    --color-border: 51 65 85;
  }
  html, body, #root { @apply h-full; }
  body { @apply bg-bg text-text antialiased; }
}
```

- [ ] **Step 4: `vite.config.ts`**:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

- [ ] **Step 5: `tsconfig.json`** — стандарт для Vite + react-jsx + strict.

- [ ] **Step 6: `index.html`** — минимум с `<div id="root"></div>` + ссылка на `/src/main.tsx`.

- [ ] **Step 7: `src/main.tsx`** + `App.tsx` — boot React + QueryClient + Router + ThemeProvider + AuthProvider (см. дальше J.2–J.3).

- [ ] **Step 8: Commit** `chore(frontend): vite + react + tailwind setup`.

### Task J.2 — ThemeContext

**Files:** `frontend/src/context/ThemeContext.tsx`

```tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark" | "system";

interface ThemeContextValue {
  theme: Theme;
  resolved: "light" | "dark";
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function resolveTheme(t: Theme): "light" | "dark" {
  if (t !== "system") return t;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    return (localStorage.getItem("theme") as Theme | null) ?? "system";
  });
  const [resolved, setResolved] = useState<"light" | "dark">(() => resolveTheme(theme));

  useEffect(() => {
    document.documentElement.classList.toggle("dark", resolved === "dark");
  }, [resolved]);

  useEffect(() => {
    localStorage.setItem("theme", theme);
    setResolved(resolveTheme(theme));
    if (theme === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = () => setResolved(resolveTheme("system"));
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, resolved, setTheme: setThemeState }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be inside ThemeProvider");
  return ctx;
}
```

`ThemeToggle.tsx`:

```tsx
import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const next = theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
  const Icon = theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;
  return (
    <button
      onClick={() => setTheme(next)}
      className="rounded-md p-2 hover:bg-surface text-muted hover:text-text transition"
      aria-label={`Сменить тему (сейчас: ${theme})`}
    >
      <Icon className="w-5 h-5" />
    </button>
  );
}
```

Commit `feat(frontend): theme context + toggle`.

### Task J.3 — AuthContext + API client

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/config.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/api/admin.ts`
- Create: `frontend/src/context/AuthContext.tsx`

`client.ts`:

```ts
import axios from "axios";

export const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      if (!location.pathname.startsWith("/login")) {
        location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);
```

`config.ts`:
```ts
import { api } from "./client";

export interface PublicConfig {
  app_name: string;
  yandex_enabled: boolean;
}

export async function fetchConfig(): Promise<PublicConfig> {
  const { data } = await api.get<PublicConfig>("/config");
  return data;
}
```

`auth.ts` — `login`, `me`, `changePassword`, `yandexStartUrl`, `yandexCallback`.

`admin.ts` — `listUsers`, `createUser`, `updateUser`, `resetPassword`, `deleteUser`.

`AuthContext.tsx` хранит `user` и `config`, выставляет `login`/`logout`, читает `/me` при наличии token.

Commit `feat(frontend): api client + auth context`.

### Task J.4 — Routes + ProtectedRoute + AppLayout

**Files:**
- Create: `frontend/src/routes.tsx`
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Create: `frontend/src/components/AppLayout.tsx`

`routes.tsx`:

```tsx
import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { HelloPage } from "./pages/HelloPage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";
import { YandexCallbackPage } from "./pages/YandexCallbackPage";
import { UsersPage } from "./pages/admin/UsersPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/oauth/yandex", element: <YandexCallbackPage /> },
  {
    path: "/",
    element: <ProtectedRoute><AppLayout /></ProtectedRoute>,
    children: [
      { index: true, element: <HelloPage /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "admin/users", element: <ProtectedRoute role="admin"><UsersPage /></ProtectedRoute> },
    ],
  },
]);
```

`ProtectedRoute` — пропускает если `user` есть; если `role` указан — проверяет.
`AppLayout` — `<header>` (имя + ThemeToggle + Logout) + `<nav>` (Hello / Profile / [Users — admin only]) + `<Outlet/>`.

Commit `feat(frontend): routing + layout + ProtectedRoute`.

---

## Chunk K — Frontend pages

### Task K.1 — LoginPage

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { fetchConfig } from "../api/config";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, config } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("Неверный email или пароль");
    }
  }

  return (
    <div className="min-h-full flex items-center justify-center bg-bg">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm bg-surface border border-border rounded-lg p-6 shadow-sm space-y-4"
      >
        <h1 className="text-xl font-semibold text-text">{config?.app_name ?? "Login"}</h1>
        <input
          type="email" placeholder="Email"
          value={email} onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
        />
        <input
          type="password" placeholder="Пароль"
          value={password} onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
        />
        {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
        <button
          type="submit"
          className="w-full rounded-md bg-primary text-white py-2 font-medium hover:opacity-90"
        >
          Войти
        </button>
        {config?.yandex_enabled && (
          <a
            href="/api/v1/auth/yandex/start"
            className="block text-center text-sm text-primary hover:underline"
          >
            Войти через Яндекс
          </a>
        )}
      </form>
    </div>
  );
}
```

### Task K.2 — HelloPage + ProfilePage

`HelloPage.tsx` — `<div className="p-8 text-text">Hello, {user.full_name}!</div>`.

`ProfilePage.tsx` — форма смены пароля; если `user.has_password` — поле `current_password` обязательно, иначе скрыто.

### Task K.3 — admin/UsersPage

Таблица users + modal Create (email + full_name + role + password) + modal Edit (full_name + role + is_active + reset password) + кнопка soft-delete.

### Task K.4 — YandexCallbackPage

```tsx
import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function YandexCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { refreshMe } = useAuth();
  useEffect(() => {
    const code = params.get("code");
    if (!code) { navigate("/login"); return; }
    api.get(`/auth/yandex/callback?code=${code}`).then(async (r) => {
      localStorage.setItem("token", r.data.access_token);
      await refreshMe();
      navigate("/");
    }).catch(() => navigate("/login?yandex_failed=1"));
  }, [params, navigate, refreshMe]);
  return <div className="p-8 text-text">Авторизация через Яндекс…</div>;
}
```

Commit `feat(frontend): pages — login/hello/profile/admin-users/yandex-callback`.

### Task K.5 — Playwright e2e

`frontend/tests/e2e/smoke.spec.ts`:

```ts
import { test, expect } from "@playwright/test";

test("admin can login, see users, switch theme", async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[type=email]', "admin@example.com");
  await page.fill('input[type=password]', "admin");
  await page.click('button[type=submit]');
  await expect(page).toHaveURL("/");
  await page.click('text=Users');
  await expect(page.locator("table")).toBeVisible();
  // тема
  await page.click('[aria-label*="Сменить тему"]');
  await expect(page.locator("html")).toHaveClass(/dark/);
});
```

Commit `test(frontend): playwright smoke (login + admin + theme)`.

---

## Chunk L — Seed admin + smoke

### Task L.1 — scripts/seed_admin.py

```python
"""Создаёт первого admin'а из SEED_ADMIN_EMAIL/SEED_ADMIN_PASSWORD."""

import asyncio
import os

from sqlalchemy import select

from src.db.session import async_session_maker
from src.models.user import User, UserRole
from src.services.auth import hash_password


async def main() -> None:
    email = os.environ.get("SEED_ADMIN_EMAIL", "admin@example.com")
    password = os.environ.get("SEED_ADMIN_PASSWORD", "admin")
    async with async_session_maker() as s:
        existing = await s.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"admin {email} already exists")
            return
        s.add(
            User(
                email=email,
                full_name="Admin",
                role=UserRole.ADMIN,
                password_hash=hash_password(password),
                is_active=True,
            )
        )
        await s.commit()
        print(f"created admin {email}")


if __name__ == "__main__":
    asyncio.run(main())
```

Commit `feat(seed): admin seed script`.

---

## Chunk M — Deploy (K8s/Kustomize)

### Task M.1 — namespace + configmap + secret

`deploy/k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: app
```

`configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: app
data:
  APP_NAME: "ai_fastapi_starter"
  DEBUG: "false"
  APP_BASE_URL: "https://example.com"
  LOG_LEVEL: "INFO"
  YANDEX_OAUTH_ENABLED: "false"
  YANDEX_REDIRECT_URI: "https://example.com/oauth/yandex"
  OPENAI_BASE_URL: "https://api.openai.com/v1"
  OPENAI_DEFAULT_MODEL: "gpt-4o-mini"
  S3_BUCKET_NAME: "app"
  S3_REGION: "ru-1"
```

`secret.example.yaml` — шаблон без значений; реальные ставит админ.

### Task M.2 — Deployments + Services

`app.yaml`, `worker.yaml`, `frontend.yaml` — каждое содержит Deployment + Service. Образцы у hrai (`deploy/k8s/app.yaml`, `ai-worker.yaml`).

### Task M.3 — Ingress + Migrate Job + ServiceMonitor

`ingress.yaml` — nginx-ingress + TLS через cert-manager (нужен annotation `cert-manager.io/cluster-issuer: letsencrypt-prod`).

`migrate-job.yaml` — Job, бежит при каждом deploy.

`monitoring/servicemonitor.yaml` — для kube-prometheus-stack.

### Task M.4 — kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: app
resources:
  - namespace.yaml
  - configmap.yaml
  - secret.example.yaml
  - migrate-job.yaml
  - app.yaml
  - worker.yaml
  - frontend.yaml
  - ingress.yaml
  - monitoring/servicemonitor.yaml
```

Commit `feat(deploy): kustomize for k8s timeweb`.

---

## Chunk N — Docs

### Task N.1 — README.md

Структура:
* Что это / для чего
* Quick start: `git clone … && cp .env.example .env && docker compose up`
* Структура каталогов (краткая)
* Auth: login + Yandex (как включить флаг)
* Темы: ссылка на AGENTS.md
* Деплой на Timeweb: пошагово (создать кластер, кубконтекст, `kubectl apply -k deploy/k8s`)
* Кастомизация: как переименовать проект (`ai_fastapi_starter` → `<your>`)

### Task N.2 — AGENTS.md

Разделы:
1. **Tooling и стиль:** Python 3.14, ruff, mypy strict, типы, docstrings русские, pre-commit.
2. **Тесты:** в Docker (`docker compose run --rm test pytest`), `pytest-asyncio` mode auto, savepoint-based фикстура `db_session`.
3. **Миграции:** Alembic, naming `YYYY_MM_DD_<rev>_<slug>.py`. Не запускаем DDL в `lifespan`.
4. **Settings:** все таймауты и магические числа через `Field` в `*Settings`. Никаких `time.sleep(60)`.
5. **Тема (light/dark)** — *тот блок из спеки секции 6.2 AGENTS.md*.
6. **Логи:** JSON через `logging_config`, корреляция через `current_operation`.
7. **Auth-гейтинг фич:** новый внешний интегратор — добавляем флаг `<NAME>_ENABLED` в Settings + `_ensure_<name>_enabled()` хелпер, который возвращает 404. Фронт читает `/api/v1/config`.

Commit `docs: README + AGENTS`.

### Task N.3 — final spec/plan move

Перенести `docs/specs/` и `docs/plans/` в финальное место. По желанию — `.gitignore` для будущих superpowers spec'ов.

Commit `docs: finalize project docs layout`.

---

## Self-Review

* [ ] Все спеки секций (1–13) покрыты тасками: ✅ модели — Chunk B; auth — D+E; admin API — F; main+config endpoint — G; worker — H; tests — I; frontend (включая темы) — J+K; deploy — M; docs (включая AGENTS.md тема) — N.
* [ ] Placeholder scan: нет TBD/TODO внутри шагов.
* [ ] Type consistency: `UserOut`/`AdminUserOut` имеют `has_password`/`has_yandex` — везде корректно.
* [ ] Темы: ThemeContext + Toggle + AGENTS.md — все три точки соединены.
* [ ] `YANDEX_OAUTH_ENABLED` — бэк (G) гасит 404, `/config` отдаёт флаг, фронт (K.1) скрывает кнопку.
* [ ] Смена пароля: `/auth/password` (D.3) + ProfilePage (K.2) + `current_password` опционален если `password_hash IS NULL`.

---

## Execution Handoff

После аппрува плана → исполнение через **superpowers:subagent-driven-development**:

* По одному subagent'у на каждый Task (A.1 → A.2 → … → N.3).
* После каждого Task — spec compliance review + code quality review.
* Каждый chunk — отдельный PR в `main` (так репо растёт читаемой историей).

Альтернатива — `superpowers:executing-plans` (batch в одной сессии).
