from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.job_description_repository import JobDescriptionRepository
from app.schemas.jd import JobDescriptionCreate, JobDescriptionRead, JobDescriptionUploadResponse


class JobDescriptionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.jd_repo = JobDescriptionRepository(db)

    async def save_job_description(
        self,
        user: User,
        payload: JobDescriptionCreate,
    ) -> JobDescriptionUploadResponse:
        job_description = await self.jd_repo.upsert(
            user_id=user.id,
            content=payload.content,
            title=payload.title,
        )
        content = job_description.content
        return JobDescriptionUploadResponse(
            id=job_description.id,
            title=job_description.title,
            content_preview=content[:500],
            character_count=len(content),
            updated_at=job_description.updated_at,
        )

    async def get_job_description(self, user_id: UUID) -> JobDescriptionRead:
        job_description = await self.jd_repo.get_by_user_id(user_id)
        if job_description is None:
            return JobDescriptionRead(
                id=None,
                title=None,
                content=None,
                content_preview=None,
                character_count=0,
                has_job_description=False,
                updated_at=None,
            )

        content = job_description.content
        return JobDescriptionRead(
            id=job_description.id,
            title=job_description.title,
            content=content,
            content_preview=content[:500],
            character_count=len(content),
            has_job_description=True,
            updated_at=job_description.updated_at,
        )

    async def delete_job_description(self, user_id: UUID) -> None:
        deleted = await self.jd_repo.delete_by_user_id(user_id)
        if not deleted:
            raise NotFoundError("No job description found to delete")
