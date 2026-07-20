"""Healthcheck — отвечает 200 OK когда app boot-нулся."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
