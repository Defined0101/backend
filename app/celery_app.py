# app/celery_app.py
from celery import Celery
from celery.schedules import crontab
import os

celery_app = Celery(
    "frs",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)
celery_app.conf.timezone = "UTC"

# Enable tracking of when a task starts
celery_app.conf.task_track_started = True

# Set how long the task results should be kept in the backend (in seconds).
celery_app.conf.result_expires = 3600 # 1 hour

# Automatically find and register tasks in the specified modules/folders.
# This means you don't need to manually import every task in your Celery app.

celery_app.autodiscover_tasks(["app.tasks"])

# Ensure our task modules are loaded
import app.tasks.update_embeddings

# Celery Beat: run task every 3 mins
celery_app.conf.beat_schedule = {
    "update-embeddings-every-3-min": {
        "task": "app.tasks.update_embeddings.update_recent_users_embeddings",
        "schedule": crontab(minute="*/3"),
    },
}