"""Пример pgqueuer-handler. В реальном проекте таски кладутся рядом."""

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ExamplePayload(BaseModel):
    message: str


async def handle_example(payload: bytes) -> None:
    data = ExamplePayload.model_validate_json(payload)
    logger.info("example task: %s", data.message)
