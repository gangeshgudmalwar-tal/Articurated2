"""
Structured logging setup for FastAPI app.
"""
import logging
import sys
from structlog import wrap_logger, PrintLoggerFactory

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

# Use structlog for structured logging
logger = wrap_logger(
    logging.getLogger("articurated"),
    logger_factory=PrintLoggerFactory(),
)
