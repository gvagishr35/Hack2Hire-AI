from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import AppBaseModel, MessageResponse


class ResumeUploadResponse(AppBaseModel):
    message: str = "Resume uploaded successfully"
    id: UUID
    filename: str
    text_preview: str = Field(description="First 500 characters of extracted text")
    character_count: int
    updated_at: datetime


class ResumeRead(AppBaseModel):
    id: UUID | None = None
    filename: str | None
    text_preview: str | None
    character_count: int
    has_resume: bool
    updated_at: datetime | None


class ResumeDeleteResponse(MessageResponse):
    pass
