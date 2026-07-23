# ai_fastapi_starter

Скелет backend-проекта (FastAPI + worker + DB + S3 + LLM-токены) с готовым frontend (React/TS/Tailwind с light/dark темами) и deploy-шаблоном под Timeweb K8s. Клонируй → переименуй → стартуй за полчаса.

## Что внутри

| Слой | Технологии |
|---|---|
| Backend | Python 3.14, FastAPI, SQLAlchemy 2.x async + asyncpg, PostgreSQL 18, Alembic, pgqueuer 1.0 |
| Worker | FastAPI(metrics+healthcheck) + pgqueuer entrypoints, Prometheus метрики (jobs_processed/duration/uptime) |
| Auth | JWT (HS256, bcrypt cost=12) + опциональный Yandex OAuth (одним флагом гасится на бэке и фронте) |
| LLM | openai SDK + TrackedOpenAI wrapper — пишет токены в `usage_log` после каждого chat-вызова |
| S3 | aiobotocore (MinIO на dev, Twcstorage/любой совместимый на prod) |
| Frontend | Vite 5 + React 18 + TS strict + Tailwind 3 + React Router 6 + TanStack Query 5; light/dark/system темы из коробки |
| Tests | pytest-asyncio в Docker, per-test engine + dependency_overrides, savepoint-чистая БД |
| Deploy | docker-compose для dev (db + minio + migrate + app + worker + frontend), Kustomize для Timeweb K8s (Deployments + Ingress + cert-manager + ServiceMonitor) |

## Quick start

```bash
git clone git@github.com:juntatalor/ai_fastapi_starter.git my-project
cd my-project

cp .env.example .env
# Поправь JWT_SECRET (≥32 chars), OPENAI_API_KEY (опционально), Yandex creds если будешь использовать.

# Поднять БД + миграции:
docker compose -p my-project up migrate --build

# Создать первого admin'а:
docker compose -p my-project run --rm app uv run python scripts/seed_admin.py
# → admin@example.com / admin (из SEED_ADMIN_* в .env)

# Поднять backend + frontend + worker:
docker compose -p my-project up -d

# Открыть http://localhost:5173 → войти admin@example.com / admin
```

## Структура

```
.
├── src/
│   ├── main.py                 FastAPI(create_app) + /healthcheck + /metrics
│   ├── config.py               AppSettings (Pydantic v2 BaseSettings)
│   ├── api/
│   │   ├── deps.py             get_db / get_current_user / get_current_admin
│   │   └── routes/v1/          auth / admin_users / config / healthcheck
│   ├── db/session.py           async engine + sessionmaker + Base
│   ├── models/                 User + UsageLog
│   ├── schemas/                Pydantic-схемы auth + admin
│   ├── services/               auth (bcrypt+JWT) + user + yandex_oauth
│   ├── common/                 logging_config / exceptions / retry / openai_client / s3 / queue
│   └── workers/worker/         pgqueuer entrypoint + tasks
├── frontend/
│   ├── src/
│   │   ├── api/                client (axios+interceptors) / auth / admin / config
│   │   ├── context/            AuthContext + ThemeContext (light/dark/system)
│   │   ├── components/         ProtectedRoute / AppLayout / ThemeToggle
│   │   ├── pages/              LoginPage / HelloPage / ProfilePage / YandexCallbackPage / admin/UsersPage
│   │   ├── styles/index.css    Tailwind + CSS-vars для семантических токенов
│   │   └── routes.tsx
│   ├── Dockerfile              multi-stage: node build → nginx serve
│   └── nginx.conf              /api → app, остальное — SPA
├── tests/                      conftest (db_engine + client + user_factory + auth_headers)
├── migrations/                 alembic async env + initial migration
├── docker/                     Dockerfile.app / .worker / .migrate / .test + initdb.sh
├── scripts/                    migrate.sh + seed_admin.py + pgqueuer_install.py
├── deploy/k8s/                 Kustomize (namespace/configmap/secret/Deployments/Ingress/migrate-job/ServiceMonitor)
└── docs/                       specs/ + plans/
```

## Auth flow

### Password (всегда работает)

```
POST /api/v1/auth/login {email, password} → {access_token}
GET  /api/v1/auth/me          (Bearer)    → UserOut
POST /api/v1/auth/password    (Bearer)    {current_password?, new_password}
```

`current_password` опционален если у юзера ещё нет пароля (только Yandex) — ставится впервые.

### Yandex OAuth (опционально)

Включается флагом `YANDEX_OAUTH_ENABLED=true`. На фронте кнопка «Войти через Яндекс» появляется автоматически (`/api/v1/config` отдаёт `yandex_enabled: true`).

```
GET /api/v1/auth/yandex/start         → 302 на oauth.yandex.ru
GET /api/v1/auth/yandex/callback?code= → находит User по email, обновляет yandex_id, возвращает JWT
```

Если флаг false — оба route'а возвращают 404 (не 403, чтобы со стороны не было видно фичу).

### Admin (role=admin)

```
GET    /api/v1/admin/users               → list[UserOut]
POST   /api/v1/admin/users                {email, full_name?, role, password?}
PATCH  /api/v1/admin/users/{id}           {full_name?, role?, is_active?}
POST   /api/v1/admin/users/{id}/password  {new_password}
DELETE /api/v1/admin/users/{id}           soft delete (is_active=false)
```

## Worker

```python
# src/workers/worker/tasks/my_task.py
from pydantic import BaseModel

class MyPayload(BaseModel):
    foo: str

async def handle_my_task(payload: bytes) -> None:
    data = MyPayload.model_validate_json(payload)
    ...
```

```python
# src/workers/worker/app.py — добавить в lifespan
queue.register_handler("my_task", partial(_wrap, "my_task", handle_my_task))
```

```python
# где-то в API
await queue.enqueue("my_task", MyPayload(foo="bar").model_dump_json().encode())
```

Метрики автоматически: `jobs_processed_total{task,status}` + `job_duration_seconds{task}`.

## Темы (light/dark)

См. секцию «Тема» в [`AGENTS.md`](./AGENTS.md). Кратко: используй семантические Tailwind токены (`bg-bg`, `bg-surface`, `text-text`, `text-muted`, `bg-primary`, `border-border`) — они автоматически меняются при переключении темы через `ThemeToggle` (Sun / Moon / Monitor). Без `dark:` префиксов в большинстве компонентов.

## Тесты

```bash
docker compose -p starter run --rm test uv run pytest
```

Текущий suite: 24/24 passed, coverage 65% (см. PR #9).

## Deploy на Timeweb K8s

```bash
# 1) Подготовь kustomize-патчи под свой регистри / hostname
# (REGISTRY_PLACEHOLDER / HOSTNAME_PLACEHOLDER в deploy/k8s/*.yaml)

# 2) Залей реальный Secret через kubectl (а не из repo!):
kubectl create secret generic app-env -n app \
  --from-literal=DATABASE_URL=... \
  --from-literal=JWT_SECRET=... \
  --from-literal=OPENAI_API_KEY=...

# 3) Накати манифесты:
kubectl apply -k deploy/k8s
```

Требуется в кластере: nginx-ingress + cert-manager (+ опционально kube-prometheus-stack для ServiceMonitor).

## Кастомизация под свой проект

1. Замени имя пакета `ai_fastapi_starter` → `<your_project>` в `pyproject.toml`, `frontend/package.json`, `compose project name`.
2. Добавь свои модели в `src/models/`, схемы в `src/schemas/`, services в `src/services/`.
3. Расширь Settings под свои env-vars.
4. Заведи новые pgqueuer-таски в `src/workers/worker/tasks/`.
5. Frontend: добавь страницы в `frontend/src/pages/` и роуты в `routes.tsx`.

Подробнее по конвенциям — в [`AGENTS.md`](./AGENTS.md).

## Лицензия

MIT (или замени на свою при форке).
