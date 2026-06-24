"""Создаёт первого admin'а из SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD.

Идемпотентно: если admin с таким email уже есть — печатает и выходит.
Используется при первом запуске стартера (после миграций).
"""

from __future__ import annotations

import asyncio
import os

from sqlalchemy import select

from src.db.session import async_session_maker
from src.models.user import User, UserRole
from src.services.auth import hash_password


async def main() -> None:
    email = os.environ.get("SEED_ADMIN_EMAIL", "admin@example.com")
    password = os.environ.get("SEED_ADMIN_PASSWORD", "admin")
    async with async_session_maker() as s:
        existing = await s.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"admin {email} already exists")
            return
        s.add(
            User(
                email=email,
                full_name="Admin",
                role=UserRole.ADMIN,
                password_hash=hash_password(password),
                is_active=True,
            )
        )
        await s.commit()
        print(f"created admin {email}")


if __name__ == "__main__":
    asyncio.run(main())
