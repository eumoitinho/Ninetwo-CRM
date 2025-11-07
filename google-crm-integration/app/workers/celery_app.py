"""
Celery Application

Celery app configuration for background tasks.
"""

from celery import Celery
from celery.schedules import crontab
from loguru import logger

from app.config import settings

# Create Celery app
celery_app = Celery(
    "google_crm_integration",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.workers.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'sync-all-users-data': {
        'task': 'app.workers.tasks.sync_all_users',
        'schedule': crontab(minute=f'*/{settings.sync_interval_minutes}'),  # Every N minutes
    },
}

logger.info("Celery app configured")
