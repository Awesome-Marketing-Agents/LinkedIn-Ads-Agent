"""Tests for Sprint 3: Ingestion Pipeline Optimization.

Covers:
- Freshness gate (should_sync, start/finish sync run)
- True upsert (no duplicates, preserves created_at)
- Pydantic API model validation
- Snapshot validation gate (partial batch failures)
- Config settings
"""

import sqlite3
import time
from datetime import datetime, timedelta, timezone, date
from unittest.mock import patch

import pytest
from pydantic import ValidationError as PydanticValidationError

from linkedin_action_center.models.api_models import (
    LinkedInAccount,
    LinkedInAnalyticsRow,
    LinkedInCampaign,
    LinkedInCreative,
    LinkedInDemographicRow,
)
from linkedin_action_center.storage.repository import (
    active_campaign_audit,
    finish_sync_run,
    persist_snapshot,
    should_sync,
    start_sync_run,
    table_counts,
)
from linkedin_action_center.storage.snapshot import assemble_snapshot


# ---------------------------------------------------------------------------
# Freshness gate tests
# ---------------------------------------------------------------------------

class TestFreshnessGate:
    """Tests for should_sync / start_sync_run / finish_sync_run."""

    def test_first_sync_always_needed(self, temp_db):
        """No previous sync → should_sync returns True."""
        needed, reason = should_sync("12345", db_path=temp_db)
        assert needed is True
        assert "no previous" in reason

    def test_skip_when_fresh(self, temp_db):
        """Second sync within TTL returns skipped."""
        run_id = start_sync_run("12345", db_path=temp_db)
        finish_sync_run(run_id, status="success", db_path=temp_db)

        needed, reason = should_sync("12345", db_path=temp_db)
        assert needed is False
        assert "fresh" in reason

    def test_force_bypasses_ttl(self, temp_db):
        """force=True bypasses TTL check."""
        run_id = start_sync_run("12345", db_path=temp_db)
        finish_sync_run(run_id, status="success", db_path=temp_db)

        needed, reason = should_sync("12345", force=True, db_path=temp_db)
        assert needed is True
        assert "force" in reason

    def test_stale_triggers_sync(self, temp_db):
        """Sync needed when last sync is older than TTL."""
        # Insert a sync_log entry with a very old finished_at
        conn = sqlite3.connect(str(temp_db))
        old_time = (datetime.now(tz=timezone.utc) - timedelta(hours=5)).isoformat()
        conn.execute(
            "INSERT INTO sync_log (account_id, started_at, finished_at, status, trigger) "
            "VALUES (?, ?, ?, ?, ?)",
            ("12345", old_time, old_time, "success", "test"),
        )
        conn.commit()
        conn.close()

        needed, reason = should_sync("12345", db_path=temp_db)
        assert needed is True
        assert "ago" in reason

    def test_sync_run_lifecycle(self, temp_db):
        """start_sync_run + finish_sync_run records stats."""
        run_id = start_sync_run("99", trigger="cli", db_path=temp_db)
        assert isinstance(run_id, int)

        stats = {"campaigns_fetched": 5, "creatives_fetched": 12, "api_calls_made": 8}
        finish_sync_run(run_id, status="success", stats=stats, db_path=temp_db)

        conn = sqlite3.connect(str(temp_db))
        row = conn.execute(
            "SELECT status, campaigns_fetched, creatives_fetched FROM sync_log WHERE id = ?",
            (run_id,),
        ).fetchone()
        conn.close()
        assert row[0] == "success"
        assert row[1] == 5
        assert row[2] == 12


# ---------------------------------------------------------------------------
# True upsert tests
# ---------------------------------------------------------------------------

class TestTrueUpsert:
    """Tests for ON CONFLICT upsert behaviour."""

    def test_upsert_no_duplicate(self, temp_db):
        """Same campaign upserted twice → COUNT(*) = 1."""
        snapshot = {
            "accounts": [{
                "id": 100,
                "name": "Acct",
                "status": "ACTIVE",
                "campaigns": [{
                    "id": 200,
                    "name": "Camp A",
                    "status": "ACTIVE",
                    "daily_metrics": [],
                    "creatives": [],
                }],
            }],
            "date_range": {},
        }
        persist_snapshot(snapshot, temp_db)
        persist_snapshot(snapshot, temp_db)

        counts = table_counts(temp_db)
        assert counts["ad_accounts"] == 1
        assert counts["campaigns"] == 1

    def test_upsert_updates_name(self, temp_db):
        """Second upsert with changed name updates the row."""
        snapshot = {
            "accounts": [{
                "id": 100,
                "name": "Original",
                "status": "ACTIVE",
                "campaigns": [],
            }],
            "date_range": {},
        }
        persist_snapshot(snapshot, temp_db)

        snapshot["accounts"][0]["name"] = "Updated"
        persist_snapshot(snapshot, temp_db)

        conn = sqlite3.connect(str(temp_db))
        row = conn.execute("SELECT name FROM ad_accounts WHERE id = 100").fetchone()
        conn.close()
        assert row[0] == "Updated"

    def test_upsert_metrics_no_duplicate(self, temp_db):
        """Same daily metric upserted twice → COUNT(*) = 1."""
        snapshot = {
            "accounts": [{
                "id": 100,
                "name": "Acct",
                "status": "ACTIVE",
                "campaigns": [{
                    "id": 200,
                    "name": "Camp",
                    "status": "ACTIVE",
                    "daily_metrics": [{"date": "2026-02-01", "impressions": 100}],
                    "creatives": [],
                }],
            }],
            "date_range": {},
        }
        persist_snapshot(snapshot, temp_db)
        persist_snapshot(snapshot, temp_db)

        counts = table_counts(temp_db)
        assert counts["campaign_daily_metrics"] == 1


# ---------------------------------------------------------------------------
# Pydantic API model tests
# ---------------------------------------------------------------------------

class TestPydanticModels:
    """Tests for LinkedIn API Pydantic models."""

    def test_valid_account(self):
        acct = LinkedInAccount.model_validate({
            "id": 123, "name": "Test", "status": "ACTIVE",
        })
        assert acct.id == 123
        assert acct.test is False

    def test_account_extra_fields_ignored(self):
        acct = LinkedInAccount.model_validate({
            "id": 1, "name": "X", "status": "ACTIVE",
            "unknownField": "value", "anotherOne": 42,
        })
        assert acct.id == 1
        assert not hasattr(acct, "unknownField")

    def test_account_missing_required_field(self):
        with pytest.raises(PydanticValidationError):
            LinkedInAccount.model_validate({"id": 1, "name": "X"})  # missing status

    def test_valid_campaign(self):
        camp = LinkedInCampaign.model_validate({
            "id": 456,
            "name": "Campaign 1",
            "status": "ACTIVE",
            "costType": "CPC",
            "dailyBudget": {"amount": "100.00", "currencyCode": "USD"},
            "offsiteDeliveryEnabled": True,
        })
        assert camp.id == 456
        assert camp.cost_type == "CPC"
        assert camp.offsite_delivery_enabled is True
        assert camp.daily_budget is not None
        assert camp.daily_budget.amount == "100.00"

    def test_valid_creative(self):
        cr = LinkedInCreative.model_validate({
            "id": "urn:li:sponsoredCreative:789",
            "campaign": "urn:li:sponsoredCampaign:456",
            "intendedStatus": "ACTIVE",
            "isServing": True,
            "content": {"reference": "urn:li:share:123"},
            "createdAt": 1700000000000,
        })
        assert cr.is_serving is True
        assert cr.content.reference == "urn:li:share:123"

    def test_analytics_row_cost_coercion(self):
        """String cost values are coerced to float."""
        row = LinkedInAnalyticsRow.model_validate({
            "pivotValues": ["urn:li:sponsoredCampaign:1"],
            "impressions": 1000,
            "clicks": 50,
            "costInLocalCurrency": "123.45",
        })
        assert row.cost_in_local_currency == 123.45

    def test_analytics_row_none_cost(self):
        """None cost is coerced to 0.0."""
        row = LinkedInAnalyticsRow.model_validate({
            "pivotValues": [],
            "costInLocalCurrency": None,
        })
        assert row.cost_in_local_currency == 0.0

    def test_demographic_row(self):
        row = LinkedInDemographicRow.model_validate({
            "pivotValues": ["Software Engineer"],
            "impressions": 500,
            "clicks": 25,
        })
        assert row.impressions == 500


# ---------------------------------------------------------------------------
# Snapshot validation gate tests
# ---------------------------------------------------------------------------

class TestSnapshotValidation:
    """Tests for the validation gate in assemble_snapshot."""

    def test_partial_batch_failure(self):
        """Invalid accounts are skipped, valid ones processed."""
        accounts = [
            {"id": 1, "name": "Good", "status": "ACTIVE"},
            {"name": "NoId", "status": "ACTIVE"},        # missing id
            {"id": 3, "name": "Good2", "status": "ACTIVE"},
        ]
        snapshot = assemble_snapshot(
            accounts=accounts,
            campaigns_list=[],
            creatives_list=[],
            camp_metrics=[],
            creat_metrics=[],
            demo_data={},
            date_start=date(2026, 1, 1),
            date_end=date(2026, 2, 1),
        )
        # Only the 2 valid accounts should appear
        assert len(snapshot["accounts"]) == 2
        ids = [a["id"] for a in snapshot["accounts"]]
        assert 1 in ids
        assert 3 in ids

    def test_all_valid_passes_through(self):
        """All valid items pass through unchanged."""
        accounts = [{"id": 1, "name": "OK", "status": "ACTIVE"}]
        campaigns = [{"id": 10, "name": "C", "status": "ACTIVE", "_account_id": 1}]
        snapshot = assemble_snapshot(
            accounts=accounts,
            campaigns_list=campaigns,
            creatives_list=[],
            camp_metrics=[],
            creat_metrics=[],
            demo_data={},
            date_start=date(2026, 1, 1),
            date_end=date(2026, 2, 1),
        )
        assert len(snapshot["accounts"]) == 1
        assert len(snapshot["accounts"][0]["campaigns"]) == 1


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestConfig:
    """Tests for Pydantic BaseSettings config."""

    def test_freshness_ttl_default(self):
        from linkedin_action_center.core.config import settings
        assert settings.freshness_ttl_minutes == 240

    def test_database_url_format(self):
        from linkedin_action_center.core.config import settings
        assert settings.database_url.startswith("sqlite:///")

    def test_backward_compat_aliases(self):
        from linkedin_action_center.core.config import (
            BASE_DIR, DATA_DIR, DATABASE_FILE, SNAPSHOT_DIR,
        )
        assert BASE_DIR.exists()
        assert DATA_DIR.exists()
        assert SNAPSHOT_DIR.exists()
        assert str(DATABASE_FILE).endswith("linkedin_ads.db")


# ---------------------------------------------------------------------------
# Database schema tests
# ---------------------------------------------------------------------------

class TestDatabaseSchema:
    """Tests for the updated database schema."""

    def test_sync_log_table_exists(self, temp_db):
        conn = sqlite3.connect(str(temp_db))
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sync_log'"
        )
        assert cur.fetchone() is not None
        conn.close()

    def test_all_tables_present(self, temp_db):
        conn = sqlite3.connect(str(temp_db))
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = {row[0] for row in cur.fetchall()}
        conn.close()

        expected = {
            "ad_accounts", "campaigns", "creatives",
            "campaign_daily_metrics", "creative_daily_metrics",
            "audience_demographics", "sync_log",
        }
        assert expected.issubset(tables)
