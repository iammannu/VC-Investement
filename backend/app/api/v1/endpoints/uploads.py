from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
import structlog

from app.core.deps import DB, CurrentUser
from app.core.storage import upload_file
from app.models.startup import Startup, StartupStatus
from app.models.document import Document, DocumentType, DocumentStatus
from app.schemas.startup import StartupResponse

router = APIRouter()
logger = structlog.get_logger(__name__)

ALLOWED_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/deck", response_model=StartupResponse, status_code=status.HTTP_201_CREATED)
async def upload_pitch_deck(
    file: UploadFile = File(..., description="Startup pitch deck (PDF)"),
    website_url: str | None = Form(None),
    current_user: CurrentUser = ...,
    db: DB = ...,
):
    if file.content_type not in ALLOWED_CONTENT_TYPES and not (
        file.filename or "").endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted",
        )

    file_data = await file.read()
    if len(file_data) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_SIZE_BYTES // 1024 // 1024}MB limit",
        )

    # Create startup record
    startup = Startup(
        owner_id=current_user.id,
        website_url=website_url,
        status=StartupStatus.PENDING,
    )
    db.add(startup)
    await db.flush()  # Get startup.id

    # Upload to MinIO
    storage_key = upload_file(
        file_data=file_data,
        content_type="application/pdf",
        filename=file.filename,
        folder=f"startups/{startup.id}",
    )

    # Create document record
    document = Document(
        startup_id=startup.id,
        doc_type=DocumentType.PITCH_DECK,
        original_name=file.filename,
        storage_key=storage_key,
        file_size_bytes=len(file_data),
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(startup)

    logger.info(
        "deck_uploaded",
        startup_id=str(startup.id),
        filename=file.filename,
        size_kb=len(file_data) // 1024,
    )
    return startup


@router.post("/{startup_id}/website", response_model=dict)
async def add_website_url(
    startup_id: UUID,
    website_url: str = Form(...),
    current_user: CurrentUser = ...,
    db: DB = ...,
):
    result = await db.execute(
        select(Startup).where(Startup.id == startup_id, Startup.owner_id == current_user.id)
    )
    startup = result.scalar_one_or_none()
    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Startup not found")

    startup.website_url = website_url
    await db.commit()

    # Create website document placeholder
    doc = Document(
        startup_id=startup.id,
        doc_type=DocumentType.WEBSITE,
        source_url=website_url,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.commit()

    return {"message": "Website URL added", "startup_id": str(startup_id)}
