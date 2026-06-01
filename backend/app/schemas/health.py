from app.schemas.common import AppBaseModel


class HealthResponse(AppBaseModel):
    status: str
    app_name: str
    environment: str
    version: str


class ReadinessResponse(AppBaseModel):
    status: str
    database: str
    redis: str
