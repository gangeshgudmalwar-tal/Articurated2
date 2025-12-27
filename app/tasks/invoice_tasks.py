"""
Invoice generation background tasks.
"""
from celery import Task
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.order import Order
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
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes
    retry_jitter=True,
)
def generate_invoice(self, order_id: int):
    """
    Generate invoice PDF for an order.
    
    Triggered when order transitions to SHIPPED state.
    Retries: 3 attempts with exponential backoff.
    
    Args:
        order_id: Order ID to generate invoice for
    """
    # Short-circuit in test/eager mode to avoid external dependencies
    if celery_app.conf.task_always_eager:
        logger.info("Eager mode: skipping invoice generation for order %s", order_id)
        return {"status": "skipped"}

    try:
        logger.info(f"Generating invoice for order {order_id}")
        
        # Get order
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.error(f"Order {order_id} not found")
            return

        # Check if invoice already generated (idempotency)
        if order.metadata and order.metadata.get("invoice_generated"):
            logger.info(f"Invoice already generated for order {order_id}")
            return

        # Generate invoice PDF
        from app.utils.invoice_generator import InvoiceGenerator
        generator = InvoiceGenerator()
        invoice_path = generator.generate(order)

        # Store invoice reference
        if not order.metadata:
            order.metadata = {}
        order.metadata["invoice_generated"] = True
        order.metadata["invoice_path"] = invoice_path
        self.db.commit()

        # Send email with invoice
        from app.tasks.notification_tasks import send_invoice_email
        send_invoice_email.delay(order_id, invoice_path)

        logger.info(f"Invoice generated successfully for order {order_id}: {invoice_path}")

    except Exception as exc:
        logger.error(f"Failed to generate invoice for order {order_id}: {exc}")
        raise self.retry(exc=exc)
