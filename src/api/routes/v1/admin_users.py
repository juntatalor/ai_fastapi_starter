"""CRUD /admin/users — только role=admin."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_admin, get_db
from src.common.exceptions import ConflictError, NotFoundError
from src.models.user import User
from src.schemas.admin import (
    AdminResetPassword,
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
)
from src.services.user import (
    create_user,
    get_user_by_id,
    list_users,
    reset_password,
    soft_delete,
    update_user,
)

router = APIRouter(prefix="/admin/users", tags=["admin"])


def _to_out(u: User) -> AdminUserOut:
    """Шорткат — оставлен для совместимости с существующими вызовами."""
    return AdminUserOut.from_user(u)


@router.get("", response_model=list[AdminUserOut])
async def list_(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
) -> list[AdminUserOut]:
    users = await list_users(db, limit=limit)
    return [_to_out(u) for u in users]


@router.post("", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_(
    body: AdminUserCreate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    try:
        user = await create_user(
            db,
            email=body.email,
            full_name=body.full_name,
            role=body.role,
            password=body.password,
        )
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return _to_out(user)


@router.patch("/{user_id}", response_model=AdminUserOut)
async def update_(
    user_id: int,
    body: AdminUserUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    try:
        user = await get_user_by_id(db, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail="user") from e
    user = await update_user(
        db, user=user, full_name=body.full_name, role=body.role, is_active=body.is_active
    )
    return _to_out(user)


@router.post("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_(
    user_id: int,
    body: AdminResetPassword,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await get_user_by_id(db, user_id)
    await reset_password(db, user=user, new_password=body.new_password)
    return Response(status_code=204)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_(
    user_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await get_user_by_id(db, user_id)
    await soft_delete(db, user=user)
    return Response(status_code=204)
