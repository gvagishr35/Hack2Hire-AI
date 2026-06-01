from uuid import UUID

from sqlalchemy import select

from app.models.job_description import JobDescription
from app.repositories.base import BaseRepository


class JobDescriptionRepository(BaseRepository):
    async def get_by_user_id(self, user_id: UUID) -> JobDescription | None:
        result = await self.db.execute(
            select(JobDescription).where(JobDescription.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: UUID,
        content: str,
        title: str | None = None,
    ) -> JobDescription:
        job_description = await self.get_by_user_id(user_id)
        if job_description is None:
            job_description = JobDescription(user_id=user_id)
            self.db.add(job_description)

        job_description.content = content.strip()
        job_description.title = title.strip() if title else None

        await self.db.flush()
        await self.db.refresh(job_description)
        return job_description

    async def delete_by_user_id(self, user_id: UUID) -> bool:
        job_description = await self.get_by_user_id(user_id)
        if job_description is None:
            return False
        await self.db.delete(job_description)
        await self.db.flush()
        return True
