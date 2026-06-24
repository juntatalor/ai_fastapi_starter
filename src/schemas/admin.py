"""Admin-схемы для /admin/users."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import User, UserRole


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    has_password: bool
    has_yandex: bool

    @classmethod
    def from_user(cls, user: User) -> "AdminUserOut":
        """Конвертация ORM User → AdminUserOut с явным маппингом полей.

        Не используем ``**user.__dict__`` — он тащит SQLAlchemy-внутренности
        и password_hash. Explicit > implicit (см. также UserOut.from_user)."""
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            has_password=user.password_hash is not None,
            has_yandex=user.yandex_id is not None,
        )


class AdminUserCreate(BaseModel):
    model_config = ConfigDict(frozen=True)
    email: EmailStr
    full_name: str | None = None
    role: UserRole = UserRole.USER
    password: str | None = Field(
        default=None, min_length=8, description="Опционально — если не задан, юзер войдёт через Yandex."
    )


class AdminUserUpdate(BaseModel):
    model_config = ConfigDict(frozen=True)
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class AdminResetPassword(BaseModel):
    model_config = ConfigDict(frozen=True)
    new_password: str = Field(min_length=8, max_length=128)
