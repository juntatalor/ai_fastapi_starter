"""ContextVars для correlation между логами и операциями."""

from contextvars import ContextVar

current_operation: ContextVar[str | None] = ContextVar("current_operation", default=None)
