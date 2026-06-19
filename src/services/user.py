"""User-сервис для admin-операций."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import ConflictError, NotFoundError
from src.models.user import User, UserRole
from src.services.auth import hash_password


async def list_users(db: AsyncSession, *, limit: int = 100) -> list[User]:
    result = await db.execute(select(User).order_by(User.id.desc()).limit(limit))
    return list(result.scalars())


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("user")
    return user


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    full_name: str | None,
    role: UserRole,
    password: str | None,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        role=role,
        password_hash=hash_password(password) if password else None,
        is_active=True,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise ConflictError(f"email {email} занят") from e
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    *,
    user: User,
    full_name: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> User:
    if full_name is not None:
        user.full_name = full_name
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    await db.commit()
    return user


async def reset_password(db: AsyncSession, *, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    await db.commit()


async def soft_delete(db: AsyncSession, *, user: User) -> None:
    user.is_active = False
    await db.commit()
