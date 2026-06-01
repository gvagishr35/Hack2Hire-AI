from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.interview_ai import generate_interview_questions, score_interview, score_single_answer
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.settings import settings
from app.models.interview import (
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
    InterviewStatus,
)
from app.models.user import User
from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.interview import (
    InterviewAnalyticsRead,
    InterviewAnswerRead,
    InterviewListItem,
    InterviewQuestionRead,
    InterviewReportRead,
    InterviewSessionRead,
    InterviewStartResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.adaptive_engine import next_difficulty, should_terminate_early


class InterviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.interview_repo = InterviewRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.jd_repo = JobDescriptionRepository(db)

    async def start_interview(self, user: User) -> InterviewStartResponse:
        active = await self.interview_repo.get_active_session(user.id)
        if active is not None:
            raise ConflictError("You already have an interview in progress. Please complete it first.")

        profile = await self.profile_repo.get_by_user_id(user.id)
        if profile is None or not profile.resume_text:
            raise BadRequestError("Upload your resume before starting an interview.")

        job_description = await self.jd_repo.get_by_user_id(user.id)
        if job_description is None or not job_description.content:
            raise BadRequestError("Save a job description before starting an interview.")

        question_count = settings.interview_question_count
        generated = await generate_interview_questions(
            resume_text=profile.resume_text,
            job_description=job_description.content,
            job_title=job_description.title,
            question_count=question_count,
        )

        first_difficulty = generated[0].get("difficulty", "easy") if generated else "easy"

        session = InterviewSession(
            user_id=user.id,
            status=InterviewStatus.IN_PROGRESS,
            total_questions=question_count,
            current_question_index=0,
            time_per_question_seconds=settings.interview_question_time_seconds,
            current_difficulty=first_difficulty,
        )
        session = await self.interview_repo.create_session(session)

        questions = [
            InterviewQuestion(
                session_id=session.id,
                question_index=index,
                question_text=item["question"],
                category=item.get("category"),
                difficulty=item.get("difficulty", "easy"),
            )
            for index, item in enumerate(generated)
        ]
        await self.interview_repo.add_questions(questions)

        return InterviewStartResponse(
            session_id=session.id,
            total_questions=session.total_questions,
            time_per_question_seconds=session.time_per_question_seconds,
            current_question_index=session.current_question_index,
            current_difficulty=session.current_difficulty,
            status=session.status,
        )

    async def get_session(self, session_id: UUID, user_id: UUID) -> InterviewSessionRead:
        session = await self._get_user_session(session_id, user_id)
        return self._session_to_read(session)

    async def submit_answer(
        self,
        session_id: UUID,
        user_id: UUID,
        payload: SubmitAnswerRequest,
    ) -> SubmitAnswerResponse:
        session = await self._get_user_session(session_id, user_id)
        profile = await self.profile_repo.get_by_user_id(user_id)
        job_description = await self.jd_repo.get_by_user_id(user_id)

        if session.status != InterviewStatus.IN_PROGRESS:
            raise BadRequestError("This interview is no longer accepting answers.")

        if session.current_question_index >= session.total_questions:
            raise BadRequestError("All questions have already been answered.")

        question = next(
            (q for q in session.questions if q.question_index == session.current_question_index),
            None,
        )
        if question is None:
            raise NotFoundError("Current question not found")

        if question.answer is not None:
            raise ConflictError("This question has already been answered.")

        score_result = await score_single_answer(
            question=question.question_text,
            answer=payload.answer_text.strip(),
            category=question.category,
            difficulty=question.difficulty,
            resume_text=profile.resume_text if profile else "",
            job_description=job_description.content if job_description else "",
            job_title=job_description.title if job_description else None,
            time_taken_seconds=payload.time_taken_seconds,
            time_limit_seconds=session.time_per_question_seconds,
        )

        answer_score = float(score_result.get("score", 0))
        answer = InterviewAnswer(
            session_id=session.id,
            question_id=question.id,
            answer_text=payload.answer_text.strip(),
            time_taken_seconds=payload.time_taken_seconds,
            score=answer_score,
            feedback=str(score_result.get("feedback", "")),
            score_breakdown=score_result.get("score_breakdown", {}),
        )
        await self.interview_repo.add_answer(answer)
        session = await self._get_user_session(session_id, user_id)

        scored_answers = await self._get_answer_scores(session)
        early_terminate, termination_reason = should_terminate_early(scored_answers)

        session.current_question_index += 1
        new_difficulty = next_difficulty(session.current_difficulty, answer_score)
        session.current_difficulty = new_difficulty

        next_question = next(
            (q for q in session.questions if q.question_index == session.current_question_index),
            None,
        )
        if next_question is not None:
            next_question.difficulty = new_difficulty

        is_complete = session.current_question_index >= session.total_questions

        if early_terminate and not is_complete:
            session.status = InterviewStatus.TERMINATED_EARLY
            session.terminated_early = True
            session.termination_reason = termination_reason
            session.completed_at = datetime.now(UTC)
            is_complete = True
        elif is_complete:
            session.status = InterviewStatus.COMPLETED
            session.completed_at = datetime.now(UTC)

        await self.interview_repo.update_session(session)

        if is_complete:
            await self._score_session(session, user_id)

        refreshed = await self._get_user_session(session_id, user_id)

        return SubmitAnswerResponse(
            message="Answer submitted successfully",
            session_id=session.id,
            question_index=question.question_index,
            is_complete=is_complete,
            next_question_index=(
                refreshed.current_question_index
                if refreshed.status == InterviewStatus.IN_PROGRESS
                else None
            ),
            status=refreshed.status,
            answer_score=answer_score,
            answer_feedback=answer.feedback,
            early_terminated=refreshed.terminated_early,
            termination_reason=refreshed.termination_reason,
            next_difficulty=new_difficulty if not is_complete else None,
        )

    async def get_report(self, session_id: UUID, user_id: UUID) -> InterviewReportRead:
        session = await self._get_user_session(session_id, user_id)

        if session.status not in (
            InterviewStatus.SCORED,
            InterviewStatus.COMPLETED,
            InterviewStatus.TERMINATED_EARLY,
        ):
            raise BadRequestError("Interview report is not ready yet.")

        if session.overall_score is None:
            await self._score_session(session, user_id)
            session = await self._get_user_session(session_id, user_id)

        if session.overall_score is None:
            raise BadRequestError("Failed to generate interview score.")

        return self._build_report(session)

    async def list_interviews(self, user_id: UUID) -> list[InterviewListItem]:
        sessions = await self.interview_repo.list_sessions_for_user(user_id)
        return [
            InterviewListItem(
                id=s.id,
                status=s.status,
                overall_score=s.overall_score,
                readiness_score=s.readiness_score,
                grade=s.grade,
                total_questions=s.total_questions,
                started_at=s.started_at,
                completed_at=s.completed_at,
                terminated_early=s.terminated_early,
            )
            for s in sessions
        ]

    async def get_analytics(self, user_id: UUID) -> InterviewAnalyticsRead:
        sessions = await self.interview_repo.list_sessions_for_user(user_id)
        scored = [
            s
            for s in sessions
            if s.status in (InterviewStatus.SCORED, InterviewStatus.TERMINATED_EARLY)
            and s.overall_score is not None
        ]

        overall_scores = [s.overall_score for s in scored if s.overall_score is not None]
        readiness_scores = [s.readiness_score for s in scored if s.readiness_score is not None]

        performance_totals: dict[str, list[float]] = {
            "technical": [],
            "communication": [],
            "time_management": [],
        }
        dimension_totals: dict[str, list[float]] = {}

        for session in scored:
            if session.performance_breakdown:
                for key, value in session.performance_breakdown.items():
                    normalized = key.lower().replace(" ", "_")
                    if normalized in performance_totals:
                        performance_totals[normalized].append(float(value))
            if session.dimension_scores:
                for key, value in session.dimension_scores.items():
                    dimension_totals.setdefault(key, []).append(float(value))

        score_trend = [
            {
                "session_id": str(s.id),
                "date": s.started_at.isoformat(),
                "overall_score": s.overall_score,
                "readiness_score": s.readiness_score,
            }
            for s in reversed(scored[-10:])
        ]

        return InterviewAnalyticsRead(
            total_interviews=len(sessions),
            completed_interviews=len(scored),
            average_overall_score=(
                sum(overall_scores) / len(overall_scores) if overall_scores else None
            ),
            average_readiness_score=(
                sum(readiness_scores) / len(readiness_scores) if readiness_scores else None
            ),
            score_trend=score_trend,
            performance_averages={
                key: sum(values) / len(values)
                for key, values in performance_totals.items()
                if values
            },
            dimension_averages={
                key: sum(values) / len(values) for key, values in dimension_totals.items() if values
            },
            recent_scores=[
                {
                    "id": str(s.id),
                    "overall_score": s.overall_score,
                    "readiness_score": s.readiness_score,
                    "grade": s.grade,
                    "date": s.started_at.isoformat(),
                }
                for s in scored[:5]
            ],
        )

    async def _score_session(self, session: InterviewSession, user_id: UUID) -> None:
        session = await self._get_user_session(session.id, user_id)
        profile = await self.profile_repo.get_by_user_id(user_id)
        job_description = await self.jd_repo.get_by_user_id(user_id)

        qa_pairs = []
        for question in sorted(session.questions, key=lambda q: q.question_index):
            if question.answer is None:
                continue
            qa_pairs.append(
                {
                    "question": question.question_text,
                    "answer": question.answer.answer_text,
                    "difficulty": question.difficulty,
                    "category": question.category,
                    "answer_score": question.answer.score,
                    "feedback": question.answer.feedback,
                },
            )

        try:
            result = await score_interview(
                resume_text=profile.resume_text if profile else "",
                job_description=job_description.content if job_description else "",
                job_title=job_description.title if job_description else None,
                qa_pairs=qa_pairs,
                terminated_early=session.terminated_early,
            )
            session.overall_score = float(result.get("overall_score", 0))
            session.readiness_score = float(result.get("readiness_score", session.overall_score))
            session.grade = str(result.get("grade", "N/A"))
            session.summary = str(result.get("summary", ""))
            session.strengths = result.get("strengths", [])
            session.weaknesses = result.get("weaknesses", [])
            session.improvements = result.get("improvements", [])
            session.performance_breakdown = result.get("performance_breakdown", {})
            session.dimension_scores = result.get("dimension_scores", {})
            session.status = InterviewStatus.SCORED
            session.scored_at = datetime.now(UTC)
        except Exception:
            session.status = InterviewStatus.FAILED
            raise

        await self.interview_repo.update_session(session)

    async def _get_answer_scores(self, session: InterviewSession) -> list[float]:
        scores: list[float] = []
        for question in sorted(session.questions, key=lambda q: q.question_index):
            if question.answer is not None and question.answer.score is not None:
                scores.append(question.answer.score)
        return scores

    async def _get_user_session(self, session_id: UUID, user_id: UUID) -> InterviewSession:
        session = await self.interview_repo.get_session_for_user(session_id, user_id)
        if session is None:
            raise NotFoundError("Interview session not found")
        return session

    def _session_to_read(self, session: InterviewSession) -> InterviewSessionRead:
        return InterviewSessionRead(
            id=session.id,
            status=session.status,
            total_questions=session.total_questions,
            current_question_index=session.current_question_index,
            time_per_question_seconds=session.time_per_question_seconds,
            current_difficulty=session.current_difficulty,
            current_question=self._get_current_question(session),
            answered_count=len(session.answers),
            started_at=session.started_at,
            completed_at=session.completed_at,
            terminated_early=session.terminated_early,
        )

    def _get_current_question(self, session: InterviewSession) -> InterviewQuestionRead | None:
        if session.status != InterviewStatus.IN_PROGRESS:
            return None
        if session.current_question_index >= session.total_questions:
            return None

        question = next(
            (q for q in session.questions if q.question_index == session.current_question_index),
            None,
        )
        if question is None:
            return None

        return InterviewQuestionRead(
            id=question.id,
            question_index=question.question_index,
            question_text=question.question_text,
            category=question.category,
            difficulty=question.difficulty,
        )

    def _build_report(self, session: InterviewSession) -> InterviewReportRead:
        questions = [
            InterviewQuestionRead(
                id=q.id,
                question_index=q.question_index,
                question_text=q.question_text,
                category=q.category,
                difficulty=q.difficulty,
            )
            for q in sorted(session.questions, key=lambda item: item.question_index)
        ]

        answers: list[InterviewAnswerRead] = []
        for q in sorted(session.questions, key=lambda item: item.question_index):
            if q.answer:
                answers.append(
                    InterviewAnswerRead(
                        id=q.answer.id,
                        question_index=q.question_index,
                        answer_text=q.answer.answer_text,
                        time_taken_seconds=q.answer.time_taken_seconds,
                        submitted_at=q.answer.submitted_at,
                        score=q.answer.score,
                        feedback=q.answer.feedback,
                        score_breakdown=q.answer.score_breakdown,
                    ),
                )

        return InterviewReportRead(
            session_id=session.id,
            status=session.status,
            overall_score=session.overall_score or 0,
            readiness_score=session.readiness_score or session.overall_score or 0,
            grade=session.grade or "N/A",
            summary=session.summary or "",
            strengths=session.strengths or [],
            weaknesses=session.weaknesses or [],
            improvements=session.improvements or [],
            dimension_scores=session.dimension_scores or {},
            performance_breakdown=session.performance_breakdown or {},
            questions=questions,
            answers=answers,
            scored_at=session.scored_at,
            completed_at=session.completed_at,
            terminated_early=session.terminated_early,
            termination_reason=session.termination_reason,
        )
