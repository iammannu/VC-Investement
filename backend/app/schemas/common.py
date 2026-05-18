from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
