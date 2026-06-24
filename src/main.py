"""FastAPI entry-point."""

import logging
from contextlib import asynccontextmanager
from logging.config import dictConfig

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.routes.v1 import admin_users, auth
from src.api.routes.v1 import config as config_route
from src.api.routes.v1 import healthcheck
from src.common.logging_config import get_logging_config
from src.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    dictConfig(get_logging_config(get_settings().log_level))
    logging.getLogger(__name__).info("App started: %s", get_settings().app_name)
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=s.app_name, debug=s.debug, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    app.include_router(healthcheck.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(admin_users.router, prefix="/api/v1")
    app.include_router(config_route.router, prefix="/api/v1")
    return app


app = create_app()
