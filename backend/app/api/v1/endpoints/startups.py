from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
import structlog

from app.core.deps import DB, CurrentUser
from app.models.startup import Startup
from app.schemas.startup import StartupResponse, StartupListItem

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/", response_model=list[StartupListItem])
async def list_startups(
    current_user: CurrentUser,
    db: DB,
    skip: int = 0,
    limit: int = 20,
):
    result = await db.execute(
        select(Startup)
        .where(Startup.owner_id == current_user.id)
        .order_by(Startup.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{startup_id}", response_model=StartupResponse)
async def get_startup(startup_id: UUID, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Startup).where(Startup.id == startup_id, Startup.owner_id == current_user.id)
    )
    startup = result.scalar_one_or_none()
    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Startup not found")
    return startup


@router.delete("/{startup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_startup(startup_id: UUID, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Startup).where(Startup.id == startup_id, Startup.owner_id == current_user.id)
    )
    startup = result.scalar_one_or_none()
    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Startup not found")

    await db.delete(startup)
    await db.commit()
    logger.info("startup_deleted", startup_id=str(startup_id))
