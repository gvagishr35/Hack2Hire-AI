from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.interview import InterviewStatus
from app.schemas.common import AppBaseModel


class InterviewQuestionRead(AppBaseModel):
    id: UUID
    question_index: int
    question_text: str
    category: str | None
    difficulty: str | None = "easy"


class InterviewAnswerRead(AppBaseModel):
    id: UUID
    question_index: int
    answer_text: str
    time_taken_seconds: int
    submitted_at: datetime
    score: float | None = None
    feedback: str | None = None
    score_breakdown: dict[str, Any] | None = None


class InterviewStartResponse(AppBaseModel):
    message: str = "Interview started successfully"
    session_id: UUID
    total_questions: int
    time_per_question_seconds: int
    current_question_index: int
    current_difficulty: str = "easy"
    status: InterviewStatus


class InterviewSessionRead(AppBaseModel):
    id: UUID
    status: InterviewStatus
    total_questions: int
    current_question_index: int
    time_per_question_seconds: int
    current_difficulty: str = "easy"
    current_question: InterviewQuestionRead | None
    answered_count: int
    started_at: datetime
    completed_at: datetime | None
    terminated_early: bool = False


class SubmitAnswerRequest(AppBaseModel):
    answer_text: str = Field(min_length=1, max_length=10000)
    time_taken_seconds: int = Field(ge=0, le=3600)


class SubmitAnswerResponse(AppBaseModel):
    message: str
    session_id: UUID
    question_index: int
    is_complete: bool
    next_question_index: int | None
    status: InterviewStatus
    answer_score: float | None = None
    answer_feedback: str | None = None
    early_terminated: bool = False
    termination_reason: str | None = None
    next_difficulty: str | None = None


class InterviewReportRead(AppBaseModel):
    session_id: UUID
    status: InterviewStatus
    overall_score: float
    readiness_score: float
    grade: str
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]
    dimension_scores: dict[str, Any]
    performance_breakdown: dict[str, Any]
    questions: list[InterviewQuestionRead]
    answers: list[InterviewAnswerRead]
    scored_at: datetime | None
    completed_at: datetime | None
    terminated_early: bool = False
    termination_reason: str | None = None


class InterviewListItem(AppBaseModel):
    id: UUID
    status: InterviewStatus
    overall_score: float | None
    readiness_score: float | None
    grade: str | None
    total_questions: int
    started_at: datetime
    completed_at: datetime | None
    terminated_early: bool = False


class InterviewAnalyticsRead(AppBaseModel):
    total_interviews: int
    completed_interviews: int
    average_overall_score: float | None
    average_readiness_score: float | None
    score_trend: list[dict[str, Any]]
    performance_averages: dict[str, float]
    dimension_averages: dict[str, float]
    recent_scores: list[dict[str, Any]]
