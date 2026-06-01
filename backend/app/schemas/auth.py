from pydantic import Field

from app.schemas.common import AppBaseModel
from app.schemas.user import UserRead


class LoginRequest(AppBaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(AppBaseModel):
    refresh_token: str


class TokenResponse(AppBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenResponse):
    user: UserRead
