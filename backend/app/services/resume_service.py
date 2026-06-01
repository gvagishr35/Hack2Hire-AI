from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.settings import settings
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.schemas.resume import ResumeRead, ResumeUploadResponse
from app.utils.pdf_extractor import extract_text_from_pdf

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
}


class ResumeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.profile_repo = ProfileRepository(db)

    async def upload_resume(self, user: User, file: UploadFile) -> ResumeUploadResponse:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise BadRequestError("Only PDF files are allowed")

        filename = file.filename or "resume.pdf"
        if not filename.lower().endswith(".pdf"):
            raise BadRequestError("File must have a .pdf extension")

        file_bytes = await file.read()
        max_bytes = settings.max_resume_size_mb * 1024 * 1024
        if len(file_bytes) == 0:
            raise BadRequestError("Uploaded file is empty")
        if len(file_bytes) > max_bytes:
            raise BadRequestError(f"File size exceeds {settings.max_resume_size_mb}MB limit")

        resume_text = extract_text_from_pdf(file_bytes)
        profile = await self.profile_repo.upsert_resume(
            user_id=user.id,
            resume_text=resume_text,
            resume_filename=filename,
            resume_content_type=file.content_type or "application/pdf",
        )

        preview = resume_text[:500]
        return ResumeUploadResponse(
            id=profile.id,
            filename=filename,
            text_preview=preview,
            character_count=len(resume_text),
            updated_at=profile.updated_at,
        )

    async def get_resume(self, user_id: UUID) -> ResumeRead:
        profile = await self.profile_repo.get_by_user_id(user_id)
        if profile is None or not profile.resume_text:
            return ResumeRead(
                id=profile.id if profile else None,
                filename=None,
                text_preview=None,
                character_count=0,
                has_resume=False,
                updated_at=None,
            )

        text = profile.resume_text
        return ResumeRead(
            id=profile.id,
            filename=profile.resume_filename,
            text_preview=text[:500],
            character_count=len(text),
            has_resume=True,
            updated_at=profile.updated_at,
        )

    async def delete_resume(self, user_id: UUID) -> None:
        deleted = await self.profile_repo.delete_by_user_id(user_id)
        if not deleted:
            raise NotFoundError("No resume found to delete")
