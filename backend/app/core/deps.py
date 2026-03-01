"""FastAPI dependency injection."""

from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session

from app.core.db import engine
from app.core.security import AuthManager


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_auth() -> AuthManager:
    return AuthManager()
