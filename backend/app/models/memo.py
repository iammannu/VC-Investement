import enum
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, JSON, Boolean, Integer, Numeric, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import Base, TimestampMixin


class MemoStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"


class Recommendation(str, enum.Enum):
    STRONG_INVEST = "strong_invest"
    INVEST = "invest"
    WATCH = "watch"
    PASS = "pass"


class ResearchType(str, enum.Enum):
    MARKET = "market"
    COMPETITOR = "competitor"
    FOUNDER = "founder"
    FUNDING = "funding"
    NEWS = "news"


# ── Research Data ──────────────────────────────────────────
class ResearchData(Base, TimestampMixin):
    __tablename__ = "research_data"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    research_type: Mapped[ResearchType] = mapped_column(
        SAEnum(ResearchType, name="research_type"), nullable=False
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSON)
    model_used: Mapped[str | None] = mapped_column(String(100))
    tokens_used: Mapped[int | None] = mapped_column(Integer)

    startup: Mapped["Startup"] = relationship("Startup", back_populates="research_data")


# ── Investment Memo ────────────────────────────────────────
class Memo(Base, TimestampMixin):
    __tablename__ = "memos"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[MemoStatus] = mapped_column(
        SAEnum(MemoStatus, name="memo_status"),
        default=MemoStatus.GENERATING,
        nullable=False,
        index=True,
    )
    recommendation: Mapped[Recommendation | None] = mapped_column(
        SAEnum(Recommendation, name="recommendation")
    )
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    total_tokens_used: Mapped[int | None] = mapped_column(Integer)
    generation_time_seconds: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)

    startup: Mapped["Startup"] = relationship("Startup", back_populates="memos")
    sections: Mapped[list["MemoSection"]] = relationship(
        "MemoSection",
        back_populates="memo",
        cascade="all, delete-orphan",
        order_by="MemoSection.section_order",
    )


# ── Memo Section ───────────────────────────────────────────
class MemoSection(Base, TimestampMixin):
    __tablename__ = "memo_sections"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    memo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("memos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_key: Mapped[str] = mapped_column(String(100), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)        # Markdown prose
    content_json: Mapped[dict | None] = mapped_column(JSON)  # Structured tables/matrices
    citations: Mapped[list | None] = mapped_column(JSON)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)

    memo: Mapped["Memo"] = relationship("Memo", back_populates="sections")


# ── Analysis Job ───────────────────────────────────────────
class AnalysisJob(Base, TimestampMixin):
    __tablename__ = "analysis_jobs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255))
    current_step: Mapped[str | None] = mapped_column(String(100))
    steps_completed: Mapped[list] = mapped_column(JSON, default=list)
    total_steps: Mapped[int] = mapped_column(Integer, default=7)
    error_message: Mapped[str | None] = mapped_column(Text)
    memo_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("memos.id"))

    startup: Mapped["Startup"] = relationship("Startup", back_populates="analysis_jobs")
