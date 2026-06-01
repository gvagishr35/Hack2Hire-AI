from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class MessageResponse(AppBaseModel):
    message: str


class ErrorDetail(AppBaseModel):
    code: str
    message: str


class ErrorResponse(AppBaseModel):
    error: ErrorDetail
