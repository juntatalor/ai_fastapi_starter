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
