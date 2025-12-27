"""
Email sending utility.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from app.config import settings
from app.database import SessionLocal
from app.models.order import Order
from app.models.return_request import ReturnRequest
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """Send emails via SMTP."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_address = settings.EMAIL_FROM

    def send_email(
        self,
        to_address: str,
        subject: str,
        html_body: str,
        attachments: list[str] = None,
    ):
        """
        Send an email via SMTP.
        
        Args:
            to_address: Recipient email address
            subject: Email subject
            html_body: HTML email body
            attachments: List of file paths to attach
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = to_address
            msg["Subject"] = subject

            msg.attach(MIMEText(html_body, "html"))

            # Add attachments
            if attachments:
                for file_path in attachments:
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=Path(file_path).name)
                    part["Content-Disposition"] = f'attachment; filename="{Path(file_path).name}"'
                    msg.attach(part)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_address}: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email to {to_address}: {e}")
            raise

    def send_invoice(self, order_id: int, invoice_path: str):
        """Send invoice email to customer."""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"Order {order_id} not found")
                return

            # TODO: Get customer email from customer service
            to_address = f"{order.customer_id}@example.com"

            subject = f"Your Invoice - Order #{order.id}"
            body = f"""
            <html>
            <body>
                <h2>Order Shipped!</h2>
                <p>Your order #{order.id} has been shipped.</p>
                <p>Tracking Number: {order.tracking_number}</p>
                <p>Carrier: {order.carrier}</p>
                <p>Please find your invoice attached.</p>
                <p>Thank you for shopping with ArtiCurated!</p>
            </body>
            </html>
            """

            self.send_email(to_address, subject, body, attachments=[invoice_path])
        finally:
            db.close()

    def send_refund_confirmation(self, return_id: int, transaction_id: str):
        """Send refund confirmation email."""
        db = SessionLocal()
        try:
            return_request = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
            if not return_request:
                logger.error(f"Return request {return_id} not found")
                return

            # TODO: Get customer email
            to_address = f"{return_request.requested_by}@example.com"

            subject = f"Refund Processed - Return #{return_id}"
            body = f"""
            <html>
            <body>
                <h2>Refund Processed</h2>
                <p>Your refund for return request #{return_id} has been processed.</p>
                <p>Refund Amount: ${return_request.refund_amount}</p>
                <p>Transaction ID: {transaction_id}</p>
                <p>The refund should appear in your account within 5-7 business days.</p>
                <p>Thank you for your patience!</p>
            </body>
            </html>
            """

            self.send_email(to_address, subject, body)
        finally:
            db.close()

    def send_order_confirmation(self, order_id: int):
        """Send order confirmation email."""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"Order {order_id} not found")
                return

            to_address = f"{order.customer_id}@example.com"

            subject = f"Order Confirmation - #{order.id}"
            body = f"""
            <html>
            <body>
                <h2>Order Confirmed!</h2>
                <p>Thank you for your order #{order.id}.</p>
                <p>Total: ${order.total}</p>
                <p>We'll notify you when your order ships.</p>
            </body>
            </html>
            """

            self.send_email(to_address, subject, body)
        finally:
            db.close()
