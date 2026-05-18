from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.models.memo import MemoStatus, Recommendation


class MemoSectionResponse(BaseModel):
    id: UUID
    section_key: str
    section_order: int
    title: str
    content: str | None
    content_json: dict | None
    citations: list | None
    is_edited: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MemoSectionUpdate(BaseModel):
    content: str
    content_json: dict | None = None


class MemoResponse(BaseModel):
    id: UUID
    startup_id: UUID
    version: int
    status: MemoStatus
    recommendation: Recommendation | None
    confidence_score: Decimal | None
    total_tokens_used: int | None
    generation_time_seconds: int | None
    error_message: str | None
    sections: list[MemoSectionResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemoListItem(BaseModel):
    id: UUID
    startup_id: UUID
    status: MemoStatus
    recommendation: Recommendation | None
    confidence_score: Decimal | None
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}
