from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
import json
import asyncio
import structlog

from app.core.deps import DB, CurrentUser
from app.models.startup import Startup
from app.models.memo import AnalysisJob
from app.schemas.startup import AnalysisJobResponse
from app.tasks.analysis_tasks import run_full_analysis

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/start/{startup_id}", response_model=AnalysisJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(startup_id: UUID, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Startup).where(Startup.id == startup_id, Startup.owner_id == current_user.id)
    )
    startup = result.scalar_one_or_none()
    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Startup not found")

    # Create job record
    job = AnalysisJob(startup_id=startup_id, current_step="queued", steps_completed=[])
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch Celery task
    task = run_full_analysis.apply_async(
        args=[str(startup_id), str(job.id)],
        queue="analysis",
    )
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)

    logger.info("analysis_started", startup_id=str(startup_id), job_id=str(job.id))
    return _job_to_schema(job)


@router.get("/status/{job_id}", response_model=AnalysisJobResponse)
async def get_job_status(job_id: UUID, current_user: CurrentUser, db: DB):
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _job_to_schema(job)


@router.get("/stream/{job_id}")
async def stream_job_status(job_id: UUID, current_user: CurrentUser, db: DB):
    """Server-Sent Events stream for real-time job progress."""

    async def event_generator():
        prev_step = None
        stale_count = 0
        while True:
            result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            payload = {
                "job_id": str(job.id),
                "current_step": job.current_step,
                "steps_completed": job.steps_completed,
                "total_steps": job.total_steps,
                "memo_id": str(job.memo_id) if job.memo_id else None,
                "error": job.error_message,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if job.current_step in ("done", "failed"):
                break

            # Detect stale job (no change for 120s → abort)
            if job.current_step == prev_step:
                stale_count += 1
                if stale_count > 24:
                    yield f"data: {json.dumps({'error': 'Job timed out'})}\n\n"
                    break
            else:
                stale_count = 0
                prev_step = job.current_step

            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _job_to_schema(job: AnalysisJob) -> AnalysisJobResponse:
    return AnalysisJobResponse(
        job_id=job.id,
        startup_id=job.startup_id,
        celery_task_id=job.celery_task_id,
        current_step=job.current_step,
        steps_completed=job.steps_completed or [],
        total_steps=job.total_steps,
        memo_id=job.memo_id,
        error_message=job.error_message,
        created_at=job.created_at,
    )
