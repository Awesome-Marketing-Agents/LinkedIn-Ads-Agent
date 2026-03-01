"""SQLAlchemy engine and session factory for PostgreSQL."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False, pool_pre_ping=True)


def init_db() -> None:
    """Create all tables defined by SQLModel metadata (dev convenience)."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel session (used as a FastAPI dependency)."""
    with Session(engine) as session:
        yield session
