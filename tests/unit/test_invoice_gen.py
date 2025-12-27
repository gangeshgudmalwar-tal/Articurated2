



import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.tasks.invoice_tasks import generate_invoice
from app.utils.invoice_generator import InvoiceGenerator
from app.utils.email_sender import EmailSender
from tests.factories import OrderFactory

import os
import tempfile

@pytest.fixture(scope="function")
def db_session():
    # Use a file-based SQLite DB for integration test reliability
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

@pytest.fixture
def order_id(db_session):
    OrderFactory._meta.sqlalchemy_session = db_session
    order = OrderFactory.create()
    db_session.commit()
    return order.id

def test_generate_invoice_idempotency(order_id, db_session):
    from app.tasks.celery_app import celery_app
    import app.tasks.invoice_tasks as invoice_tasks_mod
    celery_app.conf.task_always_eager = False
    # Patch SessionLocal in invoice_tasks to use the test's session factory
    invoice_tasks_mod.SessionLocal = lambda: db_session
    with patch.object(InvoiceGenerator, 'generate', return_value="/tmp/invoice.pdf") as mock_gen, \
         patch('app.tasks.notification_tasks.send_invoice_email.delay', return_value=None) as mock_send_email:
        # Always pass only the order ID
        result1 = generate_invoice.apply(args=[order_id]).get()
        # Re-query order if needed after task
        result2 = generate_invoice.apply(args=[order_id]).get()
        assert result1["status"] == "success"
        assert result2["status"] == "already_exists"
        assert mock_gen.call_count == 1
        assert mock_send_email.call_count == 1
