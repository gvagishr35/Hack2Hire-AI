from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import AppBaseModel, MessageResponse


class JobDescriptionCreate(AppBaseModel):
    content: str = Field(min_length=20, max_length=50000)
    title: str | None = Field(default=None, max_length=255)


class JobDescriptionUploadResponse(AppBaseModel):
    message: str = "Job description saved successfully"
    id: UUID
    title: str | None
    content_preview: str
    character_count: int
    updated_at: datetime


class JobDescriptionRead(AppBaseModel):
    id: UUID | None
    title: str | None
    content: str | None
    content_preview: str | None
    character_count: int
    has_job_description: bool
    updated_at: datetime | None


class JobDescriptionDeleteResponse(MessageResponse):
    pass
