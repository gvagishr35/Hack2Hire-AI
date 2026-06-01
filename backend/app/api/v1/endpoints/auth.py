from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.auth import AuthResponse, LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserRead, UserRegister
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new candidate account",
)
async def register(payload: UserRegister, db: DbSession) -> AuthResponse:
    return await AuthService(db).register(payload)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and receive JWT tokens",
)
async def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    return await AuthService(db).login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(payload: RefreshTokenRequest, db: DbSession) -> TokenResponse:
    return await AuthService(db).refresh_tokens(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
)
async def get_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
