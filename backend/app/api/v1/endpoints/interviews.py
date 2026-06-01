from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import Response

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.interview import (
    InterviewAnalyticsRead,
    InterviewListItem,
    InterviewReportRead,
    InterviewSessionRead,
    InterviewStartResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.interview_service import InterviewService
from app.services.pdf_report_service import build_interview_pdf

router = APIRouter()


@router.post(
    "/start",
    response_model=InterviewStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new AI interview",
)
async def start_interview(current_user: CurrentUser, db: DbSession) -> InterviewStartResponse:
    return await InterviewService(db).start_interview(current_user)


@router.get(
    "/analytics",
    response_model=InterviewAnalyticsRead,
    status_code=status.HTTP_200_OK,
    summary="Dashboard analytics for interviews",
)
async def get_interview_analytics(
    current_user: CurrentUser,
    db: DbSession,
) -> InterviewAnalyticsRead:
    return await InterviewService(db).get_analytics(current_user.id)


@router.get(
    "",
    response_model=list[InterviewListItem],
    status_code=status.HTTP_200_OK,
    summary="List user's interviews",
)
async def list_interviews(current_user: CurrentUser, db: DbSession) -> list[InterviewListItem]:
    return await InterviewService(db).list_interviews(current_user.id)


@router.get(
    "/{session_id}",
    response_model=InterviewSessionRead,
    status_code=status.HTTP_200_OK,
    summary="Get interview session state",
)
async def get_interview(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> InterviewSessionRead:
    return await InterviewService(db).get_session(session_id, current_user.id)


@router.post(
    "/{session_id}/answers",
    response_model=SubmitAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit answer for current question",
)
async def submit_answer(
    session_id: UUID,
    payload: SubmitAnswerRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> SubmitAnswerResponse:
    return await InterviewService(db).submit_answer(session_id, current_user.id, payload)


@router.get(
    "/{session_id}/report",
    response_model=InterviewReportRead,
    status_code=status.HTTP_200_OK,
    summary="Get interview score report",
)
async def get_interview_report(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> InterviewReportRead:
    return await InterviewService(db).get_report(session_id, current_user.id)


@router.get(
    "/{session_id}/report/pdf",
    status_code=status.HTTP_200_OK,
    summary="Download interview report as PDF",
)
async def download_interview_report_pdf(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    service = InterviewService(db)
    report = await service.get_report(session_id, current_user.id)
    pdf_bytes = build_interview_pdf(report)
    filename = f"hack2hire-interview-{session_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
