from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, TokenResponse
from app.schemas.user import UserRead, UserRegister


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, payload: UserRegister) -> AuthResponse:
        existing = await self.user_repo.get_by_email(payload.email.lower())
        if existing is not None:
            raise ConflictError("Email already registered")

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=UserRole.CANDIDATE,
        )
        user = await self.user_repo.create(user)
        return self._build_auth_response(user)

    async def login(self, payload: LoginRequest) -> AuthResponse:
        user = await self.user_repo.get_by_email(payload.email.lower())
        if user is None or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")

        return self._build_auth_response(user)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise UnauthorizedError("Invalid or expired refresh token") from exc

        if payload.get("type") != TOKEN_TYPE_REFRESH:
            raise UnauthorizedError("Invalid token type")

        from uuid import UUID

        subject = payload.get("sub")
        if not subject:
            raise UnauthorizedError("Invalid token payload")

        user = await self.user_repo.get_by_id(UUID(subject))
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    def _build_auth_response(self, user: User) -> AuthResponse:
        return AuthResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            user=UserRead.model_validate(user),
        )
