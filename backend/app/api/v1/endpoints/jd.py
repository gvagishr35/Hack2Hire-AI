from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.common import MessageResponse
from app.schemas.jd import (
    JobDescriptionCreate,
    JobDescriptionRead,
    JobDescriptionUploadResponse,
)
from app.services.jd_service import JobDescriptionService

router = APIRouter()


@router.post(
    "/upload",
    response_model=JobDescriptionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save job description text",
)
async def upload_job_description(
    payload: JobDescriptionCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> JobDescriptionUploadResponse:
    return await JobDescriptionService(db).save_job_description(current_user, payload)


@router.get(
    "",
    response_model=JobDescriptionRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user's job description",
)
async def get_job_description(current_user: CurrentUser, db: DbSession) -> JobDescriptionRead:
    return await JobDescriptionService(db).get_job_description(current_user.id)


@router.delete(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete current user's job description",
)
async def delete_job_description(current_user: CurrentUser, db: DbSession) -> MessageResponse:
    await JobDescriptionService(db).delete_job_description(current_user.id)
    return MessageResponse(message="Job description deleted successfully")
