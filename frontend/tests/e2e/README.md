# Playwright e2e (планируется)

Smoke-сценарии после полного `docker compose -p starter up`:

1. **Auth flow:** login admin@example.com / admin → redirect на `/` → видим Hello.
2. **Theme toggle:** клик по Sun/Moon → `<html class="dark">` появляется/исчезает.
3. **Admin users:** клик «Пользователи» → таблица → создание/обновление/soft-delete.

Запуск (после установки):

```bash
cd frontend
npm install -D @playwright/test
npx playwright install chromium
npx playwright test
```
