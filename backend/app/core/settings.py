from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Hack2Hire API", alias="APP_NAME")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        alias="ENVIRONMENT",
    )
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/hack2hire",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/hack2hire",
        alias="DATABASE_URL_SYNC",
    )

    # Security
    secret_key: str = Field(
        default="change-me-to-a-long-random-secret-key",
        alias="SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    # Runtime (Docker / production)
    uvicorn_workers: int = Field(default=1, alias="UVICORN_WORKERS")

    # Uploads
    max_resume_size_mb: int = Field(default=5, alias="MAX_RESUME_SIZE_MB")

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # Interview
    interview_question_count: int = Field(default=5, alias="INTERVIEW_QUESTION_COUNT")
    interview_question_time_seconds: int = Field(
        default=120,
        alias="INTERVIEW_QUESTION_TIME_SECONDS",
    )
    interview_early_termination_avg: float = Field(
        default=25.0,
        alias="INTERVIEW_EARLY_TERMINATION_AVG",
    )
    interview_early_termination_min_answers: int = Field(
        default=2,
        alias="INTERVIEW_EARLY_TERMINATION_MIN_ANSWERS",
    )
    interview_single_answer_fail_threshold: float = Field(
        default=15.0,
        alias="INTERVIEW_SINGLE_ANSWER_FAIL_THRESHOLD",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str, info) -> str:
        environment = info.data.get("environment", "development")
        if environment == "production" and value == "change-me-to-a-long-random-secret-key":
            raise ValueError("SECRET_KEY must be set to a secure value in production")
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
