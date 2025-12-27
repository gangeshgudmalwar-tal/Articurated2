"""
Invoice PDF generation utility.
"""
from pathlib import Path
from datetime import datetime
from app.models.order import Order
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class InvoiceGenerator:
    """Generate invoice PDFs from order data."""

    def __init__(self):
        self.storage_path = Path(settings.STORAGE_PATH) / "invoices"
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def generate(self, order: Order) -> str:
        """
        Generate invoice PDF for an order.
        
        Args:
            order: Order model instance
            
        Returns:
            Path to generated invoice PDF
        """
        try:
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"invoice_{order.id}_{timestamp}.pdf"
            output_path = self.storage_path / filename

            # Render HTML template
            html_content = self._render_invoice_html(order)

            # Generate PDF using WeasyPrint
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(output_path)

            logger.info(f"Invoice generated: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to generate invoice for order {order.id}: {e}")
            raise

    def _render_invoice_html(self, order: Order) -> str:
        """
        Render invoice HTML from order data.
        
        Args:
            order: Order model instance
            
        Returns:
            HTML string
        """
        # TODO: Use Jinja2 template for better formatting
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice - Order #{order.id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .details {{ margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .totals {{ text-align: right; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>INVOICE</h1>
                <p>Order #{order.id}</p>
                <p>Date: {order.created_at.strftime('%Y-%m-%d')}</p>
            </div>
            
            <div class="details">
                <h3>Customer Information</h3>
                <p>Customer ID: {order.customer_id}</p>
                <p>Shipping Address: {order.shipping_address.get('street', '')}, 
                   {order.shipping_address.get('city', '')}, 
                   {order.shipping_address.get('state', '')} 
                   {order.shipping_address.get('postal_code', '')}</p>
            </div>
            
            <h3>Order Items</h3>
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"<tr><td>{item.product_name}</td><td>{item.quantity}</td><td>${item.unit_price}</td><td>${item.subtotal}</td></tr>"
                        for item in order.line_items
                    ])}
                </tbody>
            </table>
            
            <div class="totals">
                <p>Subtotal: ${order.subtotal}</p>
                <p>Tax: ${order.tax}</p>
                <p>Shipping: ${order.shipping_cost}</p>
                <p><strong>Total: ${order.total}</strong></p>
            </div>
            
            <div style="margin-top: 40px; text-align: center; color: #666;">
                <p>Thank you for your business!</p>
            </div>
        </body>
        </html>
        """
        return html
