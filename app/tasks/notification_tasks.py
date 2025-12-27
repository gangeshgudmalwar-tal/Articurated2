"""
Email notification background tasks.
"""
from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_invoice_email(self, order_id: int, invoice_path: str):
    """
    Send invoice email to customer.
    
    Args:
        order_id: Order ID
        invoice_path: Path to invoice PDF
    """
    if celery_app.conf.task_always_eager:
        logger.info("Eager mode: skipping invoice email for order %s", order_id)
        return {"status": "skipped"}

    try:
        logger.info(f"Sending invoice email for order {order_id}")
        
        # TODO: Implement email sending logic
        from app.utils.email_sender import EmailSender
        sender = EmailSender()
        sender.send_invoice(order_id, invoice_path)
        
        logger.info(f"Invoice email sent for order {order_id}")
    except Exception as exc:
        logger.error(f"Failed to send invoice email for order {order_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_refund_email(self, return_id: int, transaction_id: str):
    """
    Send refund confirmation email to customer.
    
    Args:
        return_id: Return request ID
        transaction_id: Refund transaction ID
    """
    if celery_app.conf.task_always_eager:
        logger.info("Eager mode: skipping refund email for return %s", return_id)
        return {"status": "skipped"}

    try:
        logger.info(f"Sending refund email for return {return_id}")
        
        # TODO: Implement email sending logic
        from app.utils.email_sender import EmailSender
        sender = EmailSender()
        sender.send_refund_confirmation(return_id, transaction_id)
        
        logger.info(f"Refund email sent for return {return_id}")
    except Exception as exc:
        logger.error(f"Failed to send refund email for return {return_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: int):
    """Send order confirmation email."""
    if celery_app.conf.task_always_eager:
        logger.info("Eager mode: skipping order confirmation email for order %s", order_id)
        return {"status": "skipped"}

    try:
        logger.info(f"Sending order confirmation email for order {order_id}")
        
        from app.utils.email_sender import EmailSender
        sender = EmailSender()
        sender.send_order_confirmation(order_id)
        
        logger.info(f"Order confirmation email sent for order {order_id}")
    except Exception as exc:
        logger.error(f"Failed to send order confirmation email for order {order_id}: {exc}")
        raise self.retry(exc=exc)
