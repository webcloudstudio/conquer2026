"""Celery application — scheduled turn processing."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "conquerv5",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Beat schedule: process all active worlds every 6 hours by default.
    # Admin can also trigger turns manually via POST /admin/worlds/{id}/process-turn.
    beat_schedule={
        "process-all-turns": {
            "task": "app.tasks.turn_tasks.process_all_worlds",
            "schedule": crontab(minute=0, hour="*/6"),
        },
    },
)
