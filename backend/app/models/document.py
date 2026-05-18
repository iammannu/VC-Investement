import enum
from uuid import UUID, uuid4
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, JSON, Boolean, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import Base, TimestampMixin


class DocumentType(str, enum.Enum):
    PITCH_DECK = "pitch_deck"
    WEBSITE = "website"
    SUPPLEMENTARY = "supplementary"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), nullable=False, index=True
    )

    doc_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, name="document_type"), nullable=False
    )
    original_name: Mapped[str | None] = mapped_column(String(500))
    storage_key: Mapped[str | None] = mapped_column(String(500))  # MinIO object key
    source_url: Mapped[str | None] = mapped_column(String(500))   # For website docs

    page_count: Mapped[int | None] = mapped_column(Integer)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    raw_text: Mapped[str | None] = mapped_column(Text)
    extracted_data: Mapped[dict | None] = mapped_column(JSON)
    ocr_used: Mapped[bool] = mapped_column(Boolean, default=False)
    chunks_count: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status"),
        default=DocumentStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    startup: Mapped["Startup"] = relationship("Startup", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document id={self.id} type={self.doc_type} startup={self.startup_id}>"
