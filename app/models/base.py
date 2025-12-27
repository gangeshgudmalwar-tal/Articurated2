"""
Base model utilities and common fields.
"""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.dialects.postgresql import JSONB


class JSONType(TypeDecorator):
    """Cross-dialect JSON column type.

    Uses PostgreSQL JSONB when available; falls back to generic JSON on other
    dialects (e.g., SQLite used in tests).
    """

    impl = JSONB
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        # SQLite and others
        return dialect.type_descriptor(JSON())


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )
