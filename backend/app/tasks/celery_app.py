from celery import Celery
from app.config import settings

celery_app = Celery(
    "memo_generator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.analysis_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.analysis_tasks.run_full_analysis": {"queue": "analysis"},
        "app.tasks.analysis_tasks.regenerate_memo_section": {"queue": "analysis"},
    },
    task_soft_time_limit=600,   # 10 min soft limit
    task_time_limit=720,         # 12 min hard limit
)
