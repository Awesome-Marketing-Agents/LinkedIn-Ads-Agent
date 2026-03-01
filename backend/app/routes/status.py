"""Status route: token health, database counts, campaign audit."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.deps import get_auth, get_db
from app.core.security import AuthManager
from app.crud.sync_log import active_campaign_audit, table_counts
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("")
def status(
    session: Session = Depends(get_db),
    auth: AuthManager = Depends(get_auth),
):
    token_status = auth.token_status()

    try:
        db_counts = table_counts(session)
    except Exception:
        db_counts = {"error": -1}

    try:
        audit = active_campaign_audit(session)
    except Exception:
        audit = []

    return {
        "token": token_status,
        "database": db_counts,
        "active_campaign_audit": audit,
    }
