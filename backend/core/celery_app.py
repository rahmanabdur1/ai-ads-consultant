# backend/core/celery_app.py

from celery import Celery
from core.config import settings

celery_app = Celery(
    "ai_ads",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks.campaign_tasks", "tasks.analytics_tasks", "tasks.optimization_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "run-optimization-every-6h": {
            "task": "tasks.optimization_tasks.run_optimization_all",
            "schedule": 21600.0,  # every 6 hours
        },
        "sync-analytics-every-1h": {
            "task": "tasks.analytics_tasks.sync_all_analytics",
            "schedule": 3600.0,  # every 1 hour
        },
    }
)