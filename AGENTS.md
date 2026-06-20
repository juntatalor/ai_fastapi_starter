# AGENTS.md

Инструкции для AI-агентов и людей, кто работает с этим стартером. Сохрани/обнови этот файл при форке.

## 1. Tooling и стиль

* **Python 3.14.** Никаких `from __future__ import` нужно только для перенаправления aware-типов в старом stdlib API — современный синтаксис типов работает изначально.
* **uv** для зависимостей: `uv sync`, `uv run pytest`. Лок-файл `uv.lock` в репе.
* **Ruff** + **mypy strict** через pre-commit. Запускать локально: `uv run pre-commit run --all`.
* **Line length 100** (ruff конфиг). При необходимости — точечный `# noqa: E501`, не глобально.
* **Type hints везде.** Pydantic `Field(description=...)` обязательно — это документация API + чек на code review.
* **Docstrings / комментарии на русском.** Поясняй "почему", не "что".
* **Никаких magic numbers в коде.** Любой таймаут / cap / интервал — Field в `*Settings` (см. `src/config.py`).

## 2. Тесты

* Гоняем **только в Docker**: `docker compose -p <name> run --rm test uv run pytest`.
* Backend-тесты могут идти >5 минут — таймаут в CI **600s**.
* Async: `pytest-asyncio` в режиме `auto`. Фикстуры `db_engine`, `client`, `user_factory`, `auth_headers` — в `tests/conftest.py`.
* **Per-test engine.** Не использовать module-level `async_session_maker` в тестах — asyncpg-соединение из одного event loop ломает следующий тест. Бери `db_session` фикстуру.
* Покрытие цель **≥80%** на `src/services` и `src/common`.
* Когда меняешь миграцию: `docker compose -p <name> down db -v && docker compose -p <name> up migrate` для чистой БД.

## 3. Миграции

* **Alembic async-aware.** `migrations/env.py` использует `async_engine_from_config`.
* **Naming:** `YYYY_MM_DD_<rev>_<slug>.py` (см. `alembic.ini` `file_template`).
* **DDL только в миграциях.** Никогда не вызывай `Base.metadata.create_all()` в lifespan / startup. Исключение — тестовый conftest.
* Сгенерировать миграцию: `docker compose -p <name> run --rm migrate uv run alembic revision --autogenerate -m "..."`. Просмотри — autogenerate ошибается с FK/индексами.
* Накат: `docker compose -p <name> up migrate`.

## 4. Settings

* Все env-vars в `AppSettings` (`src/config.py`) с `Field(description=...)` и валидаторами.
* Worker имеет отдельный `WorkerSettings` (`src/workers/worker/config.py`) — runtime не пересекается.
* `get_settings()` / `get_worker_settings()` декорированы `@lru_cache`. В тестах после `monkeypatch.setenv` — `get_settings.cache_clear()`.

## 5. Тема (light/dark)

Стартер поддерживает три темы (`light` / `dark` / `system`) из коробки. Конвенции:

1. **Используй семантические токены, а не палитру напрямую.** В `frontend/src/styles/index.css` определены CSS-vars (`--color-bg`, `--color-surface`, `--color-text`, `--color-text-muted`, `--color-primary`, `--color-border`), расширенные в `tailwind.config.ts` как `bg-bg`, `bg-surface`, `text-text`, `text-muted`, `bg-primary`, `border-border`. Они автоматически меняются при `.dark` на `<html>`. Пиши `bg-surface text-text` — а не `bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100`.

2. **Если нужно жёстко прописать цвет** (status badge, brand-акцент, ошибка/успех) — пиши обе ветки в одной строке: `text-red-500 dark:text-red-400`, `bg-emerald-100 dark:bg-emerald-900/40`.

3. **Не используй `text-black` / `bg-white` без `dark:` пары.** Один из режимов сломается.

4. **Перед коммитом проверь обе темы.** В шапке layout кнопка ThemeToggle (Sun/Moon/Monitor) — переключи и пройди по основным экранам. На login — иконка в правом верхнем углу (до auth-провайдера).

5. **Иконки** — `lucide-react`, наследуют `currentColor`. Тематизировать отдельно не нужно — настраивай `text-*` на родителе.

6. **Изображения с прозрачным фоном** могут быть нечитаемы в одной из тем. Лого делай в SVG с `currentColor` или клади две версии (`logo-light.svg` / `logo-dark.svg`) и переключай через `useTheme().resolved`.

7. **Playwright e2e:** переключай тему через `await page.evaluate(() => document.documentElement.classList.add('dark'))` и сравнивай скриншоты в обоих режимах.

## 6. Логи и correlation

* JSON-логгер через `src/common/logging_config.py`. В каждом log-record добавляется `op` из `current_operation` ContextVar если он установлен.
* В долгих job'ах / HTTP-запросах ставь `current_operation.set("...")` — увидишь его в логах БД, LLM-вызовов, retry-сообщениях.

## 7. Auth-гейтинг внешних фич

Когда добавляешь новую внешнюю интеграцию (новый OAuth, новый мессенджер, новый LLM-провайдер):

1. Добавь `<NAME>_ENABLED: bool = Field(default=False, description=...)` в `AppSettings`.
2. На бэке вверху эндпоинтов фичи — `_ensure_<name>_enabled()` хелпер, который при false бросает 404 (не 403).
3. В `src/api/routes/v1/config.py` добавь поле в `PublicConfig` (`<name>_enabled: bool`).
4. Фронт читает `useAuth().config?.<name>_enabled` и не рендерит соответствующую кнопку / страницу.
5. Тест: `test_<name>_disabled_returns_404`.

Эталон — Yandex OAuth (`src/services/yandex_oauth.py` + `src/api/routes/v1/auth.py`).

## 8. PR-этикет

* Одна ветка — один Chunk (или одна логическая задача).
* PR title: `<scope>: <что>`. PR body — что внутри + smoke если был.
* **Никогда не мёрджи PR без явной просьбы пользователя.** Создавать — можно, мёрджить — нельзя.
* В коммитах: `feat(scope):`, `fix(scope):`, `chore(scope):`, `test(scope):`, `docs(scope):`.

## 9. Что НЕ делать в стартере

Если ты добавляешь домен-специфичную логику (компании, мессенджеры, чат-ассистент, биллинг, специфичные модели) — это **не сюда**. Стартер должен оставаться чистым каркасом. Перенеси в проект-форк.

## 10. Куда копать дальше

* `docs/specs/2026-06-19-ai-fastapi-starter-design.md` — дизайн-документ.
* `docs/plans/2026-06-19-ai-fastapi-starter-plan.md` — implementation plan со всеми chunks.
* PR'ы #1–#13 в репе — история того, как стартер собирался.
