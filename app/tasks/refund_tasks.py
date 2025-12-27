"""
Refund processing background tasks.
"""
from celery import Task
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.return_request import ReturnRequest
from app.utils.exceptions import RetryableError
import logging

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task that provides database session."""
    
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    max_retries=5,
    default_retry_delay=120,  # 2 minutes
    retry_backoff=True,
    retry_backoff_max=1800,  # 30 minutes
    retry_jitter=True,
)
def process_refund(self, return_id: int):
    """
    Process refund for a completed return.
    
    Triggered when return transitions to COMPLETED state.
    Retries: 5 attempts with exponential backoff.
    Alerts on final failure.
    
    Args:
        return_id: Return request ID to process refund for
    """
    if celery_app.conf.task_always_eager:
        logger.info("Eager mode: skipping refund processing for return %s", return_id)
        return {"status": "skipped"}

    try:
        logger.info(f"Processing refund for return {return_id}")
        
        # Get return request
        return_request = self.db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
        if not return_request:
            logger.error(f"Return request {return_id} not found")
            return

        # Check if refund already processed (idempotency)
        if return_request.refund_transaction_id:
            logger.info(f"Refund already processed for return {return_id}")
            return

        # Process refund via payment gateway
        # TODO: Implement real payment gateway integration
        transaction_id = f"REFUND-{return_id}-{int(return_request.created_at.timestamp())}"
        
        # Store transaction ID
        return_request.refund_transaction_id = transaction_id
        if not return_request.metadata:
            return_request.metadata = {}
        return_request.metadata["refund_processed"] = True
        return_request.metadata["refund_transaction_id"] = transaction_id
        self.db.commit()

        # Send refund confirmation email
        from app.tasks.notification_tasks import send_refund_email
        send_refund_email.delay(return_id, transaction_id)

        logger.info(f"Refund processed successfully for return {return_id}: {transaction_id}")

    except Exception as exc:
        logger.error(f"Failed to process refund for return {return_id}: {exc}")
        
        # Alert on final retry
        if self.request.retries >= self.max_retries - 1:
            logger.critical(f"ALERT: Final refund retry failed for return {return_id}")
            # TODO: Send alert to operations team
        
        raise self.retry(exc=exc)
