"""Retry-helper с exponential backoff + jitter."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Запускает ``fn`` до ``attempts`` раз, ждёт ``base_delay * 2^n`` + jitter."""
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except exceptions as e:
            last_exc = e
            if attempt == attempts:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay += random.random() * 0.5
            logger.warning("retry attempt %d/%d after %.2fs: %s", attempt, attempts, delay, e)
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
