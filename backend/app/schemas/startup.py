from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from app.models.startup import StartupStatus


class StartupCreate(BaseModel):
    website_url: str | None = None


class StartupResponse(BaseModel):
    id: UUID
    name: str | None
    website_url: str | None
    industry: str | None
    stage: str | None
    geography: str | None
    founding_year: int | None
    extracted_data: dict | None
    status: StartupStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StartupListItem(BaseModel):
    id: UUID
    name: str | None
    industry: str | None
    stage: str | None
    status: StartupStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisJobResponse(BaseModel):
    job_id: UUID
    startup_id: UUID
    celery_task_id: str | None
    current_step: str | None
    steps_completed: list[str]
    total_steps: int
    memo_id: UUID | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
