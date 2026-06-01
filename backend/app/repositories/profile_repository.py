from uuid import UUID

from sqlalchemy import select

from app.models.candidate_profile import CandidateProfile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository):
    async def get_by_user_id(self, user_id: UUID) -> CandidateProfile | None:
        result = await self.db.execute(
            select(CandidateProfile).where(CandidateProfile.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def upsert_resume(
        self,
        *,
        user_id: UUID,
        resume_text: str,
        resume_filename: str,
        resume_content_type: str,
    ) -> CandidateProfile:
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            profile = CandidateProfile(user_id=user_id)
            self.db.add(profile)

        profile.resume_text = resume_text
        profile.resume_filename = resume_filename
        profile.resume_content_type = resume_content_type

        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def delete_by_user_id(self, user_id: UUID) -> bool:
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            return False
        await self.db.delete(profile)
        await self.db.flush()
        return True
