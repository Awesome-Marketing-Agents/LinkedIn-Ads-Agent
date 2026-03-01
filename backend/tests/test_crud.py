"""Tests for CRUD operations using SQLite in-memory."""

from sqlmodel import Session

from app.crud.accounts import get_accounts, upsert_account
from app.crud.campaigns import get_campaigns, upsert_campaign
from app.crud.metrics import (
    get_campaign_metrics_paginated,
    upsert_campaign_daily_metrics,
)
from app.crud.sync_log import finish_sync_run, should_sync, start_sync_run


def test_upsert_and_get_accounts(session: Session):
    upsert_account(session, {"id": 1, "name": "Test Account", "status": "ACTIVE"})
    session.commit()

    accounts = get_accounts(session)
    assert len(accounts) == 1
    assert accounts[0].name == "Test Account"


def test_upsert_account_update(session: Session):
    upsert_account(session, {"id": 1, "name": "Old Name", "status": "ACTIVE"})
    session.commit()
    upsert_account(session, {"id": 1, "name": "New Name", "status": "PAUSED"})
    session.commit()

    accounts = get_accounts(session)
    assert len(accounts) == 1
    assert accounts[0].name == "New Name"
    assert accounts[0].status == "PAUSED"


def test_upsert_campaign(session: Session):
    # Need account first for FK
    upsert_account(session, {"id": 100, "name": "Acct", "status": "ACTIVE"})
    session.commit()

    camp = {
        "id": 1, "name": "Test Campaign", "status": "ACTIVE",
        "settings": {"daily_budget": "50", "cost_type": "CPC"},
    }
    upsert_campaign(session, 100, camp)
    session.commit()

    campaigns = get_campaigns(session)
    assert len(campaigns) == 1
    assert campaigns[0]["name"] == "Test Campaign"
    assert campaigns[0]["account_name"] == "Acct"


def test_upsert_campaign_daily_metrics(session: Session):
    upsert_account(session, {"id": 100, "name": "Acct", "status": "ACTIVE"})
    session.commit()
    upsert_campaign(session, 100, {"id": 1, "name": "Camp", "status": "ACTIVE", "settings": {}})
    session.commit()

    camp = {
        "id": 1,
        "daily_metrics": [
            {"date": "2026-01-01", "impressions": 1000, "clicks": 50, "spend": 25.0},
            {"date": "2026-01-02", "impressions": 1200, "clicks": 60, "spend": 30.0},
        ],
    }
    upsert_campaign_daily_metrics(session, camp)
    session.commit()

    result = get_campaign_metrics_paginated(session)
    assert result["total"] == 2
    assert len(result["rows"]) == 2


def test_sync_log_lifecycle(session: Session):
    need_sync, reason = should_sync(session, "12345")
    assert need_sync is True
    assert "no previous" in reason

    run_id = start_sync_run(session, "12345")
    assert run_id is not None

    finish_sync_run(session, run_id, status="success", stats={"campaigns_fetched": 5})

    # After successful sync, should not need sync (within TTL)
    need_sync, reason = should_sync(session, "12345")
    assert need_sync is False
    assert "fresh" in reason


def test_force_sync(session: Session):
    run_id = start_sync_run(session, "12345")
    finish_sync_run(session, run_id, status="success")

    need_sync, reason = should_sync(session, "12345", force=True)
    assert need_sync is True
    assert "force" in reason
