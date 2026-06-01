from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app import __version__
from app.core.dependencies import DbSession
from app.core.settings import settings
from app.database.redis import check_redis_connection
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.environment,
        version=__version__,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    responses={503: {"description": "Service unavailable"}},
)
async def readiness_check(db: DbSession) -> ReadinessResponse:
    database_status = "disconnected"
    redis_status = "disconnected"

    try:
        await db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"database": "disconnected", "redis": redis_status},
        ) from None

    try:
        if await check_redis_connection():
            redis_status = "connected"
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"database": database_status, "redis": "disconnected"},
        ) from None

    return ReadinessResponse(
        status="ok",
        database=database_status,
        redis=redis_status,
    )
