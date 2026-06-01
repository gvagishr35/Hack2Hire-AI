from fastapi import APIRouter, File, UploadFile, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.common import MessageResponse
from app.schemas.resume import ResumeRead, ResumeUploadResponse
from app.services.resume_service import ResumeService

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF resume and extract text",
)
async def upload_resume(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(..., description="PDF resume file"),
) -> ResumeUploadResponse:
    return await ResumeService(db).upload_resume(current_user, file)


@router.get(
    "",
    response_model=ResumeRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user's resume",
)
async def get_resume(current_user: CurrentUser, db: DbSession) -> ResumeRead:
    return await ResumeService(db).get_resume(current_user.id)


@router.delete(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete current user's resume",
)
async def delete_resume(current_user: CurrentUser, db: DbSession) -> MessageResponse:
    await ResumeService(db).delete_resume(current_user.id)
    return MessageResponse(message="Resume deleted successfully")
