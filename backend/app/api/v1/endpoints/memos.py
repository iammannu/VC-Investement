from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.core.deps import DB, CurrentUser
from app.models.startup import Startup
from app.models.memo import Memo, MemoSection, MemoStatus
from app.schemas.memo import MemoResponse, MemoListItem, MemoSectionUpdate

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/", response_model=list[MemoListItem])
async def list_memos(current_user: CurrentUser, db: DB, skip: int = 0, limit: int = 20):
    result = await db.execute(
        select(Memo)
        .join(Startup, Memo.startup_id == Startup.id)
        .where(Startup.owner_id == current_user.id)
        .order_by(Memo.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{memo_id}", response_model=MemoResponse)
async def get_memo(memo_id: UUID, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Memo)
        .options(selectinload(Memo.sections))
        .join(Startup, Memo.startup_id == Startup.id)
        .where(Memo.id == memo_id, Startup.owner_id == current_user.id)
    )
    memo = result.scalar_one_or_none()
    if not memo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    return memo


@router.patch("/{memo_id}/sections/{section_key}", response_model=dict)
async def update_section(
    memo_id: UUID,
    section_key: str,
    payload: MemoSectionUpdate,
    current_user: CurrentUser,
    db: DB,
):
    result = await db.execute(
        select(MemoSection)
        .join(Memo, MemoSection.memo_id == Memo.id)
        .join(Startup, Memo.startup_id == Startup.id)
        .where(
            MemoSection.memo_id == memo_id,
            MemoSection.section_key == section_key,
            Startup.owner_id == current_user.id,
        )
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    section.content = payload.content
    if payload.content_json:
        section.content_json = payload.content_json
    section.is_edited = True
    await db.commit()

    logger.info("section_updated", memo_id=str(memo_id), section=section_key)
    return {"message": "Section updated"}


@router.post("/{memo_id}/sections/{section_key}/regenerate", response_model=dict)
async def regenerate_section(
    memo_id: UUID,
    section_key: str,
    current_user: CurrentUser,
    db: DB,
):
    result = await db.execute(
        select(Memo)
        .join(Startup, Memo.startup_id == Startup.id)
        .where(Memo.id == memo_id, Startup.owner_id == current_user.id)
    )
    memo = result.scalar_one_or_none()
    if not memo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")

    from app.tasks.analysis_tasks import regenerate_memo_section
    task = regenerate_memo_section.apply_async(
        args=[str(memo_id), section_key], queue="analysis"
    )
    return {"message": "Regeneration queued", "task_id": task.id}


@router.delete("/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memo(memo_id: UUID, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Memo)
        .join(Startup, Memo.startup_id == Startup.id)
        .where(Memo.id == memo_id, Startup.owner_id == current_user.id)
    )
    memo = result.scalar_one_or_none()
    if not memo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    await db.delete(memo)
    await db.commit()
