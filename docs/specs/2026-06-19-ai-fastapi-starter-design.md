# ai_fastapi_starter — дизайн стартера

> **Цель:** скелет проекта, который копируется → переименовывается → стартует
> за полчаса. Содержит работающую инфраструктуру (API, worker, DB, S3, LLM,
> auth, frontend, deploy) и нулевую доменную логику.

## 1. Тех. стек

* **Backend:** Python 3.14, FastAPI, SQLAlchemy 2.x async + asyncpg, PG 18,
  Alembic, pgqueuer 1.0, aiobotocore (S3), openai SDK, Pydantic v2,
  prometheus-client, pytest + pytest-asyncio.
* **Frontend:** Vite + React 18 + TS + Tailwind + React Router + TanStack
  Query + Axios.
* **Infra:** Docker Compose (dev/single-VM), Kubernetes + Kustomize (prod
  Timeweb), Dockerfile.app / Dockerfile.worker / Dockerfile.migrate /
  Dockerfile.test, nginx-serve frontend (static).
* **Auth:** JWT (HS256) + bcrypt + опциональный Yandex OAuth (одним
  фича-флагом гасится одновременно на бэке и на фронте).

## 2. Структура репозитория

```
ai_fastapi_starter/
├── README.md                  ← «Start here»: clone / rename / first run
├── AGENTS.md                  ← инструкции для AI-ассистентов
├── pyproject.toml             ← uv-managed зависимости
├── alembic.ini, migrations/
├── .env.example, .gitignore, .pre-commit-config.yaml
├── docker-compose.yml         ← app + worker + db (PG18) + minio + migrate + test + frontend
├── docker/
│   ├── Dockerfile.app
│   ├── Dockerfile.worker
│   ├── Dockerfile.migrate
│   └── Dockerfile.test
├── src/
│   ├── main.py                ← FastAPI + /healthcheck + /metrics + lifespan
│   ├── config.py              ← AppSettings (env-driven, Pydantic v2)
│   ├── context.py             ← ContextVar(operation_id) для correlation
│   ├── api/
│   │   ├── deps.py            ← get_db, get_current_user, get_current_admin
│   │   └── routes/v1/
│   │       ├── auth.py        ← /login /me /password /yandex/start /yandex/callback
│   │       ├── admin_users.py ← /admin/users CRUD (role=admin only)
│   │       ├── config.py      ← GET /config → {yandex_enabled}
│   │       └── healthcheck.py
│   ├── db/session.py          ← engine, async_session_maker, Base
│   ├── models/
│   │   ├── user.py            ← User (email, password_hash, yandex_id, full_name, role, is_active)
│   │   └── usage_log.py       ← LLM tokens log
│   ├── schemas/
│   │   ├── auth.py
│   │   └── admin.py
│   ├── services/
│   │   ├── auth.py            ← bcrypt + JWT
│   │   ├── user.py            ← CRUD для admin
│   │   └── yandex_oauth.py    ← code → email + yandex_id + name
│   ├── common/
│   │   ├── logging_config.py  ← JSON-лог + correlation
│   │   ├── exceptions.py
│   │   ├── retry.py
│   │   ├── openai_client.py   ← TrackedOpenAI (usage_log)
│   │   ├── queue/             ← pgqueuer adapter
│   │   └── s3/                ← aiobotocore client
│   └── workers/worker/
│       ├── main.py, app.py    ← FastAPI(metrics-only) + pgqueuer
│       ├── config.py
│       ├── metrics.py         ← jobs_processed_total, job_duration_seconds
│       └── tasks/example_task.py
├── scripts/
│   ├── seed_admin.py          ← создаёт первого admin'а
│   └── seed_users.py          ← (опц.) демо-юзеры
├── tests/
│   ├── conftest.py
│   ├── api/test_healthcheck.py
│   ├── api/test_auth.py
│   ├── api/test_admin_users.py
│   └── workers/test_example_task.py
├── frontend/
│   ├── package.json, vite.config.ts, tailwind.config.ts, index.html
│   ├── Dockerfile
│   └── src/
│       ├── main.tsx, App.tsx, routes.tsx
│       ├── api/
│       │   ├── client.ts, auth.ts, config.ts, admin.ts
│       ├── context/
│       │   ├── AuthContext.tsx
│       │   └── ThemeContext.tsx
│       ├── pages/
│       │   ├── LoginPage.tsx
│       │   ├── YandexCallbackPage.tsx
│       │   ├── HelloPage.tsx
│       │   ├── ProfilePage.tsx        ← смена пароля
│       │   └── admin/UsersPage.tsx
│       ├── components/
│       │   ├── ProtectedRoute.tsx
│       │   ├── AppLayout.tsx
│       │   └── ThemeToggle.tsx
│       └── styles/index.css           ← Tailwind @tailwind base/components/utilities + tokens
└── deploy/k8s/
    ├── kustomization.yaml
    ├── namespace.yaml, configmap.yaml, secret.example.yaml
    ├── app.yaml, worker.yaml, frontend.yaml, ingress.yaml, migrate-job.yaml
    └── monitoring/servicemonitor.yaml
```

## 3. Модели данных

### 3.1 User

| Поле          | Тип          | Описание                                              |
|---------------|--------------|-------------------------------------------------------|
| id            | int PK       |                                                       |
| email         | str UNIQUE   | login и адрес                                         |
| password_hash | str NULL     | bcrypt; NULL если входит только через Yandex          |
| yandex_id     | str NULL UQ  | связка с Yandex-аккаунтом                             |
| full_name     | str NULL     | имя для UI                                            |
| role          | enum         | `user` (default) / `admin`                            |
| is_active     | bool         | soft-delete (false → не login'ится)                   |
| created_at    | timestamptz  | server-default `now()`                                |

Никаких company, manager_id, отделов — это домен.

### 3.2 UsageLog

| Поле               | Тип       | Описание                                |
|--------------------|-----------|-----------------------------------------|
| id                 | int PK    |                                         |
| user_id            | int FK    | NULL для system-вызовов из worker       |
| operation          | str       | произвольный тэг (`chat`, `embed`, ...) |
| model              | str       | LLM model name                          |
| prompt_tokens      | int       |                                         |
| completion_tokens  | int       |                                         |
| total_tokens       | int       |                                         |
| created_at         | timestamp |                                         |

`TrackedOpenAI` пишет сюда из `on_llm_end` callback или через middleware.
Биллинг/квоты — домен, в стартер не входят.

## 4. API

### 4.1 Auth (`/api/v1/auth`)

| Метод | Endpoint              | Описание                                                                                          | Гейтинг          |
|-------|-----------------------|---------------------------------------------------------------------------------------------------|------------------|
| POST  | `/login`              | `{email, password}` → `{access_token, token_type}`                                                | always           |
| GET   | `/me`                 | текущий user                                                                                      | auth             |
| POST  | `/password`           | `{current_password?, new_password}` — смена пароля юзером.                                        | auth             |
| GET   | `/yandex/start`       | 302 → Yandex OAuth authorize URL                                                                  | `YANDEX_OAUTH_ENABLED` |
| GET   | `/yandex/callback`    | `?code=…` → ищет user по email, обновляет yandex_id, возвращает token                             | `YANDEX_OAUTH_ENABLED` |

**`/password` поведение:**
* если у user `password_hash` IS NOT NULL — `current_password` обязателен и проверяется;
* если NULL (только Yandex) — `current_password` опционален, ставит пароль впервые;
* новый пароль ≥ 8 символов.

**Гейтинг Yandex:** если `YANDEX_OAUTH_ENABLED=false` — оба yandex-роута
возвращают **404** (не 403 — чтобы со стороны не было видно фичу). Фронт
читает `/api/v1/config` и не рендерит кнопку.

### 4.2 Admin (`/api/v1/admin/users`)

| Метод  | Endpoint            | Body                                          | Описание                |
|--------|---------------------|-----------------------------------------------|-------------------------|
| GET    | `/`                 | -                                             | список + пагинация      |
| POST   | `/`                 | `{email, full_name?, role, password?}`        | создать                 |
| PATCH  | `/{id}`             | `{full_name?, role?, is_active?}`             | обновить                |
| POST   | `/{id}/password`    | `{new_password}`                              | сброс пароля юзеру      |
| DELETE | `/{id}`             | -                                             | soft delete (`is_active=false`) |

Все — только role=admin.

### 4.3 Config

`GET /api/v1/config` → `{yandex_enabled: bool, app_name: str}` — публичный
(без auth), фронт читает на старте.

## 5. Auth flow и безопасность

* JWT HS256, `sub` = user.id, `exp` = `JWT_TTL_DAYS` (default 7).
* `Authorization: Bearer <token>` header.
* Bcrypt cost = 12 (через `bcrypt` напрямую, без passlib).
* 401 — не auth; 403 — auth но нет прав.
* `get_current_user(token)` → User; `get_current_admin(user)` → проверка
  `role == admin`, иначе 403.

## 6. Frontend

### 6.1 Routes

| Path                  | Auth     | Role  | Страница                                  |
|-----------------------|----------|-------|-------------------------------------------|
| `/login`              | -        | -     | LoginPage (email/password + Yandex по флагу) |
| `/oauth/yandex`       | -        | -     | YandexCallbackPage (?code → /yandex/callback) |
| `/`                   | required | user+ | HelloPage («Hello, {name}»)               |
| `/profile`            | required | user+ | смена пароля                              |
| `/admin/users`        | required | admin | UsersPage (таблица + Create/Edit modal)   |

`ProtectedRoute` редиректит на `/login` без token и на 403 при нехватке роли.

### 6.2 Light/Dark тема

**Архитектура:**

* `tailwind.config.ts`: `darkMode: 'class'`.
* `ThemeContext` хранит `theme: 'light' | 'dark' | 'system'`. Persist в
  `localStorage['theme']`. По default — `'system'`, читает
  `matchMedia('(prefers-color-scheme: dark)')`.
* `useEffect` в ThemeContext: добавляет/убирает класс `dark` на
  `document.documentElement` в зависимости от resolved theme.
* `ThemeToggle` в `AppLayout` header — 3-state кнопка (Sun / Moon / Auto).
* На `LoginPage` (до auth) тема тоже работает — `ThemeProvider` оборачивает
  всё `App.tsx`.

**Дизайн-токены** через CSS-vars + `@layer base` в `styles/index.css`:

```css
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
  body {
    @apply bg-[rgb(var(--color-bg))] text-[rgb(var(--color-text))];
  }
}
```

Tailwind config расширяет `colors.surface`, `colors.primary` через эти vars
— тогда `bg-surface` и `text-primary` работают без `dark:`-веток в JSX.

**В AGENTS.md** добавим раздел «Тема»:

```markdown
## Тема (light/dark)

Стартер поддерживает обе темы из коробки. Конвенции:

1. **Используй семантические токены, а не палитру напрямую.**
   `bg-surface` / `text-primary` / `border-border` — а не `bg-white` /
   `text-indigo-500`. Токены определены в `frontend/src/styles/index.css`
   через CSS-vars и расширены в `tailwind.config.ts`.

2. **Если нужно жёстко прописать цвет** (badge, status, brand-акцент) —
   пиши обе ветки: `bg-emerald-100 dark:bg-emerald-900/40`.

3. **Не используй `text-black` / `bg-white` без `dark:` пары.** Один из
   двух режимов сломается.

4. **Перед коммитом проверь обе темы.** В верхней панели — переключатель
   Sun / Moon / Auto. Прогон Playwright обоих режимов
   (`page.evaluate(() => document.documentElement.classList.add('dark'))`).

5. **Иконки** — `lucide-react`, наследуют `currentColor`, отдельно
   тематизировать не нужно.

6. **Изображения с прозрачным фоном** — могут быть нечитаемы. Если есть
   логотип — клади две версии или SVG с `currentColor`.
```

## 7. Worker

* FastAPI(metrics-only) на отдельном порту 8001 для `/healthcheck` +
  `/metrics`.
* pgqueuer.Queue с handler-ами, регистрируемыми через `register_handler`.
* Каждый task — Pydantic-payload schema + handler-функция; пример
  `tasks/example_task.py` рассылает «hello world» в лог.
* Periodic tasks (опц.) — через `asyncio.create_task` в lifespan; пример
  не закладываем, но в README показываем как добавить.
* Метрики: `jobs_processed_total{task,status}` Counter,
  `job_duration_seconds{task}` Histogram, `worker_uptime_seconds` Gauge.

## 8. LLM integration

* `src/common/openai_client.py`: `TrackedOpenAI` — wrapper над `AsyncOpenAI`
  который записывает usage в `usage_log` после каждого вызова.
* env-vars: `OPENAI_API_KEY`, `OPENAI_BASE_URL` (для DeepSeek и т.п.),
  `OPENAI_DEFAULT_MODEL`, `OPENAI_CHAT_TIMEOUT_SECONDS`.
* Никаких langchain — это специфика чат-агентов; в стартере оставим
  только сырой SDK с трекингом.

## 9. S3

* `src/common/s3/client.py`: aiobotocore client, env: `S3_ENDPOINT_URL`,
  `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`,
  `S3_REGION`.
* На dev — minio в compose; в prod — Twcstorage / любой S3-совместимый.
* Helper'ы: `upload_bytes`, `download_bytes`, `presigned_get_url`,
  `delete_object`.

## 10. Deploy

### 10.1 docker-compose.yml

Сервисы: `db`, `minio`, `migrate` (one-shot), `app`, `worker`,
`frontend` (build → nginx сервит static), `test` (manual run).

### 10.2 Kubernetes (Timeweb)

`deploy/k8s/`:

* `namespace.yaml` + `configmap.yaml` + `secret.example.yaml` (без
  реальных секретов; реальные кладёт админ через GH Actions OIDC или
  вручную).
* Deployment'ы `app`, `worker`, `frontend` + Service для каждого.
* `migrate-job.yaml` — Job, бежит до Deployment'ов.
* `ingress.yaml` — nginx-ingress + cert-manager (TLS).
* `monitoring/servicemonitor.yaml` — для kube-prometheus-stack (если
  стек уже стоит в кластере).
* В README блок «Как развернуть на Timeweb» — пошагово: создать кластер
  через Twc API, поставить nginx-ingress + cert-manager, kubectl apply -k.

## 11. Тесты

* `tests/conftest.py`: async-engine на `hrai_test`-DB (или
  `<project>_test`), savepoint-based `db_session` fixture, httpx
  AsyncClient.
* `pytest.ini` / `pyproject.toml`: `asyncio_mode = auto`,
  `addopts = --strict-markers -ra --cov`.
* В Docker: `docker compose run --rm test pytest`. Coverage цель ≥80%
  для common/services/auth.
* Frontend: Playwright e2e (опц.), один сценарий — login + admin smoke.

## 12. Что НЕ войдёт

| Не входит                       | Где взять при необходимости                       |
|---------------------------------|---------------------------------------------------|
| Companies / multi-tenancy       | домен; добавить FK `company_id` в User            |
| Messengers (Telegram/MAX)       | hrai `src/services/messengers/`                   |
| Chat-assistant (LangChain)      | hrai `src/services/chat_assistant/`               |
| Доменные сущности               | домен                                             |
| Billing / quotas                | hrai `src/services/billing*.py`                   |
| Full monitoring stack           | hrai `deploy/k8s/monitoring/`                     |
| Frontend pages кроме базовых    | домен                                             |

## 13. Дальнейшие шаги

1. **Ревью этой спеки пользователем.** После аппрува →
2. **Writing-plans** — нарезка на ~10 chunks с пошаговыми задачами
   (skeleton → DB+models → auth → admin API → worker → frontend →
   deploy → tests → README/AGENTS).
3. **Реализация** через subagent-driven-development или вручную.
4. **Push** в https://github.com/juntatalor/ai_fastapi_starter (`main` ветка).
