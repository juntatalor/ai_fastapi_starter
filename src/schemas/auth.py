"""Pydantic-схемы auth-роутов."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole


class LoginRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    email: EmailStr = Field(description="Email пользователя.")
    password: str = Field(min_length=1, description="Пароль в открытом виде (по HTTPS).")


class TokenResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    has_password: bool = Field(description="Можно ли логиниться по password.")
    has_yandex: bool = Field(description="Привязан ли Yandex-аккаунт.")


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    current_password: str | None = Field(
        default=None,
        description="Текущий пароль. Обязателен если у user'а уже есть password_hash.",
    )
    new_password: str = Field(min_length=8, max_length=128, description="Новый пароль ≥8 символов.")
