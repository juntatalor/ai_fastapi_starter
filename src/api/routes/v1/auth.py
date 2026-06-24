"""Auth routes: /login, /me, /password, и (опционально) Yandex."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.common.exceptions import NotFoundError, PermissionDeniedError
from src.models.user import User
from src.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserOut
from src.services.auth import authenticate, change_password, issue_token

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
