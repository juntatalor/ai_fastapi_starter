"""Auth routes: /login, /me, /password, и (опционально) Yandex."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.common.exceptions import NotFoundError, PermissionDeniedError
from src.config import get_settings
from src.models.user import User
from src.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserOut
from src.services.auth import authenticate, change_password, issue_token
from src.services.yandex_oauth import authorize_url, exchange_code

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        user = await authenticate(db, email=body.email, password=body.password)
    except (NotFoundError, PermissionDeniedError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    return TokenResponse(access_token=issue_token(user.id))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.from_user(user)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await change_password(
            db,
            user=user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


def _ensure_yandex_enabled() -> None:
    if not get_settings().yandex_oauth_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/yandex/start")
async def yandex_start() -> RedirectResponse:
    _ensure_yandex_enabled()
    return RedirectResponse(await authorize_url(), status_code=302)


@router.get("/yandex/callback", response_model=TokenResponse)
async def yandex_callback(code: str, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    _ensure_yandex_enabled()
    info = await exchange_code(code)
    result = await db.execute(select(User).where(User.email == info.email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь не зарегистрирован. Попросите администратора добавить ваш email.",
        )
    if user.yandex_id != info.yandex_id:
        user.yandex_id = info.yandex_id
    if not user.full_name and info.display_name:
        user.full_name = info.display_name
    await db.commit()
    return TokenResponse(access_token=issue_token(user.id))
