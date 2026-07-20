"""ContextVars для correlation между логами и операциями.

Используются ContextFilter в logging_config.py — добавляются в каждую
запись лога автоматически. Заполняются HTTP-middleware (request_id /
user_id) или вручную в долгих job'ах (current_operation).
"""

from contextvars import ContextVar

# Произвольный тэг текущей операции (job / request handler / задача в очереди).
current_operation: ContextVar[str | None] = ContextVar("current_operation", default=None)

# UUID/строка request'а — обычно ставится HTTP middleware при входе запроса.
request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

# ID авторизованного пользователя — ставится middleware/dependency после auth.
user_id: ContextVar[int | None] = ContextVar("user_id", default=None)
