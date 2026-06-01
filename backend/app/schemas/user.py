from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import AppBaseModel


class UserBase(AppBaseModel):
    email: EmailStr


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserCreate(UserRegister):
    role: UserRole = UserRole.CANDIDATE


class UserRead(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
