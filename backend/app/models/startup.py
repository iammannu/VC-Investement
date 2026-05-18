import enum
from uuid import UUID, uuid4
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import Base, TimestampMixin


class StartupStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Startup(Base, TimestampMixin):
    __tablename__ = "startups"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Startup metadata (populated by AI extraction)
    name: Mapped[str | None] = mapped_column(String(255))
    website_url: Mapped[str | None] = mapped_column(String(500))
    industry: Mapped[str | None] = mapped_column(String(255))
    stage: Mapped[str | None] = mapped_column(String(100))
    geography: Mapped[str | None] = mapped_column(String(255))
    founding_year: Mapped[int | None]

    # Structured data extracted from deck
    extracted_data: Mapped[dict | None] = mapped_column(JSON)

    status: Mapped[StartupStatus] = mapped_column(
        SAEnum(StartupStatus, name="startup_status"),
        default=StartupStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="startups")
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="startup", cascade="all, delete-orphan"
    )
    memos: Mapped[list["Memo"]] = relationship(
        "Memo", back_populates="startup", cascade="all, delete-orphan"
    )
    research_data: Mapped[list["ResearchData"]] = relationship(
        "ResearchData", back_populates="startup", cascade="all, delete-orphan"
    )
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        "AnalysisJob", back_populates="startup", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Startup id={self.id} name={self.name}>"
