from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.core.deps import DB, CurrentUser
from app.models.startup import Startup
from app.models.memo import Memo
from app.services.export.pdf_exporter import generate_memo_pdf

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/memo/{memo_id}/pdf")
async def export_memo_pdf(memo_id: UUID, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Memo)
        .options(selectinload(Memo.sections), selectinload(Memo.startup))
        .join(Startup, Memo.startup_id == Startup.id)
        .where(Memo.id == memo_id, Startup.owner_id == current_user.id)
    )
    memo = result.scalar_one_or_none()
    if not memo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")

    pdf_bytes = generate_memo_pdf(memo)
    startup_name = (memo.startup.name or "startup").lower().replace(" ", "-")
    filename = f"investment-memo-{startup_name}.pdf"

    logger.info("pdf_exported", memo_id=str(memo_id))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
