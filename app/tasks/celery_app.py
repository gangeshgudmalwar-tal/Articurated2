"""
Celery application configuration.
"""
from celery import Celery
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "articurated",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.invoice_tasks",
        "app.tasks.refund_tasks",
        "app.tasks.notification_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Run tasks eagerly during tests to avoid external broker dependencies
if settings.ENVIRONMENT.lower() == "test" or settings.CELERY_TASK_ALWAYS_EAGER:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url="memory://",
        result_backend="cache+memory://",
    )

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.invoice_tasks.*": {"queue": "invoices"},
    "app.tasks.refund_tasks.*": {"queue": "refunds"},
    "app.tasks.notification_tasks.*": {"queue": "notifications"},
}
