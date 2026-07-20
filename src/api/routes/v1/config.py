"""Публичный config endpoint — фронт читает на старте."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import get_settings

router = APIRouter(prefix="/config", tags=["config"])


class PublicConfig(BaseModel):
    app_name: str
    yandex_enabled: bool


@router.get("", response_model=PublicConfig)
def get_public_config() -> PublicConfig:
    s = get_settings()
    return PublicConfig(app_name=s.app_name, yandex_enabled=s.yandex_oauth_enabled)
