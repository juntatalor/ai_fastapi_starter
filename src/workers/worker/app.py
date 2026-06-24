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
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

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

    @app.get("/metrics", include_in_schema=False)
    def _metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/healthcheck")
    def _hc() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
