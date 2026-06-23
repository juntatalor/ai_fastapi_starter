"""Smoke-тесты конфига."""

from src.config import AppSettings


def test_settings_load_with_minimal_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:y@z/db")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    s = AppSettings(_env_file=None)  # type: ignore[call-arg]
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.jwt_ttl_days == 7
    assert s.yandex_oauth_enabled is False
