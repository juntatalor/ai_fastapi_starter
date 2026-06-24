"""Auth-сервис: bcrypt + JWT. Никаких company-привязок."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import NotFoundError, PermissionDeniedError
from src.config import get_settings
from src.models.user import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def issue_token(user_id: int) -> str:
    s = get_settings()
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(days=s.jwt_ttl_days),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> int:
    s = get_settings()
    data = jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    return int(data["sub"])


async def authenticate(db: AsyncSession, *, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise NotFoundError("Неверный email или пароль")
    if user.password_hash is None:
        raise PermissionDeniedError("Войдите через Yandex или попросите admin'а сбросить пароль.")
    if not verify_password(password, user.password_hash):
        raise NotFoundError("Неверный email или пароль")
    return user


async def get_user(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("user")
    return user


async def change_password(
    db: AsyncSession, *, user: User, current_password: str | None, new_password: str
) -> None:
    if user.password_hash is not None:
        if current_password is None or not verify_password(current_password, user.password_hash):
            raise PermissionDeniedError("Текущий пароль неверен")
    user.password_hash = hash_password(new_password)
    await db.commit()
