from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview import InterviewAnswer, InterviewQuestion, InterviewSession, InterviewStatus
from app.repositories.base import BaseRepository


class InterviewRepository(BaseRepository):
    async def create_session(self, session: InterviewSession) -> InterviewSession:
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def add_questions(self, questions: list[InterviewQuestion]) -> None:
        self.db.add_all(questions)
        await self.db.flush()

    async def get_session_for_user(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> InterviewSession | None:
        result = await self.db.execute(
            select(InterviewSession)
            .where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
            .options(
                selectinload(InterviewSession.questions).selectinload(InterviewQuestion.answer),
                selectinload(InterviewSession.answers),
            ),
        )
        return result.scalar_one_or_none()

    async def list_sessions_for_user(self, user_id: UUID) -> list[InterviewSession]:
        result = await self.db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc()),
        )
        return list(result.scalars().all())

    async def add_answer(self, answer: InterviewAnswer) -> InterviewAnswer:
        self.db.add(answer)
        await self.db.flush()
        await self.db.refresh(answer)
        return answer

    async def update_session(self, session: InterviewSession) -> InterviewSession:
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_active_session(self, user_id: UUID) -> InterviewSession | None:
        result = await self.db.execute(
            select(InterviewSession).where(
                InterviewSession.user_id == user_id,
                InterviewSession.status == InterviewStatus.IN_PROGRESS,
            ),
        )
        return result.scalar_one_or_none()
