"""Yandex OAuth — code → email + yandex_id + display_name."""

from dataclasses import dataclass

import httpx

from src.common.exceptions import ExternalServiceError
from src.config import get_settings


@dataclass(frozen=True)
class YandexUserInfo:
    yandex_id: str
    email: str
    display_name: str | None


async def authorize_url() -> str:
    s = get_settings()
    return (
        "https://oauth.yandex.ru/authorize?response_type=code"
        f"&client_id={s.yandex_client_id}&redirect_uri={s.yandex_redirect_uri}"
    )


async def exchange_code(code: str) -> YandexUserInfo:
    s = get_settings()
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": s.yandex_client_id,
                "client_secret": s.yandex_client_secret,
            },
        )
        if token_resp.status_code != 200:
            raise ExternalServiceError(f"yandex token: {token_resp.text}")
        access_token = token_resp.json()["access_token"]

        user_resp = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {access_token}"},
            params={"format": "json"},
        )
        if user_resp.status_code != 200:
            raise ExternalServiceError(f"yandex user info: {user_resp.text}")
        data = user_resp.json()
        return YandexUserInfo(
            yandex_id=str(data["id"]),
            email=data.get("default_email") or "",
            display_name=data.get("real_name") or data.get("display_name"),
        )
