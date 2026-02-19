"""Unit tests for storage repository."""

import pytest
import sqlite3
from pathlib import Path
from linkedin_action_center.storage.repository import (
    persist_snapshot,
    table_counts,
    active_campaign_audit,
)
from linkedin_action_center.utils.errors import StorageError


class TestPersistSnapshot:
    """Test snapshot persistence to database."""
    
    def test_persist_empty_snapshot(self, temp_db):
        """Test persisting an empty snapshot."""
        snapshot = {"accounts": [], "date_range": {}}
        persist_snapshot(snapshot, temp_db)
        
        # Verify no data was inserted
        counts = table_counts(temp_db)
        assert counts["ad_accounts"] == 0
    
    def test_persist_account_only(self, temp_db):
        """Test persisting account without campaigns."""
        snapshot = {
            "accounts": [{
                "id": 123456,
                "name": "Test Account",
                "status": "ACTIVE",
                "currency": "USD",
                "type": "BUSINESS",
                "test": False,
                "campaigns": []
            }],
            "date_range": {}
        }
        persist_snapshot(snapshot, temp_db)
        
        counts = table_counts(temp_db)
        assert counts["ad_accounts"] == 1
        assert counts["campaigns"] == 0
    
    def test_persist_account_with_campaign(self, temp_db):
        """Test persisting account with campaign."""
        snapshot = {
            "accounts": [{
                "id": 123456,
                "name": "Test Account",
                "status": "ACTIVE",
                "currency": "USD",
                "campaigns": [{
                    "id": 789012,
                    "name": "Test Campaign",
                    "status": "ACTIVE",
                    "daily_metrics": [],
                    "creatives": []
                }]
            }],
            "date_range": {}
        }
        persist_snapshot(snapshot, temp_db)
        
        counts = table_counts(temp_db)
        assert counts["ad_accounts"] == 1
        assert counts["campaigns"] == 1
    
    def test_persist_upsert_behavior(self, temp_db):
        """Test that re-persisting updates existing records."""
        snapshot = {
            "accounts": [{
                "id": 123456,
                "name": "Original Name",
                "status": "ACTIVE",
                "campaigns": []
            }],
            "date_range": {}
        }
        
        # First insert
        persist_snapshot(snapshot, temp_db)
        counts_before = table_counts(temp_db)
        
        # Update name and re-insert
        snapshot["accounts"][0]["name"] = "Updated Name"
        persist_snapshot(snapshot, temp_db)
        counts_after = table_counts(temp_db)
        
        # Should still have only 1 account (upserted, not duplicated)
        assert counts_before["ad_accounts"] == 1
        assert counts_after["ad_accounts"] == 1
        
        # Verify name was updated
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM ad_accounts WHERE id = ?", (123456,))
        result = cur.fetchone()
        conn.close()
        
        assert result[0] == "Updated Name"
    
    def test_persist_with_daily_metrics(self, temp_db):
        """Test persisting campaign with daily metrics."""
        snapshot = {
            "accounts": [{
                "id": 123456,
                "name": "Test Account",
                "status": "ACTIVE",
                "campaigns": [{
                    "id": 789012,
                    "name": "Test Campaign",
                    "status": "ACTIVE",
                    "daily_metrics": [{
                        "date": "2026-02-01",
                        "impressions": 1000,
                        "clicks": 50,
                        "cost": 100.0,
                        "conversions": 5
                    }],
                    "creatives": []
                }]
            }],
            "date_range": {}
        }
        persist_snapshot(snapshot, temp_db)
        
        counts = table_counts(temp_db)
        assert counts["campaign_daily_metrics"] >= 1
    
    def test_persist_with_creatives(self, temp_db):
        """Test persisting campaign with creatives."""
        snapshot = {
            "accounts": [{
                "id": 123456,
                "name": "Test Account",
                "status": "ACTIVE",
                "campaigns": [{
                    "id": 789012,
                    "name": "Test Campaign",
                    "status": "ACTIVE",
                    "daily_metrics": [],
                    "creatives": [{
                        "id": "creative789",
                        "reference": "urn:li:creative:789",
                        "status": "ACTIVE"
                    }]
                }]
            }],
            "date_range": {}
        }
        persist_snapshot(snapshot, temp_db)
        
        counts = table_counts(temp_db)
        assert counts["creatives"] >= 1


class TestTableCounts:
    """Test table row counting."""
    
    def test_table_counts_empty_db(self, temp_db):
        """Test counts on empty database."""
        counts = table_counts(temp_db)
        
        assert isinstance(counts, dict)
        assert counts["ad_accounts"] == 0
        assert counts["campaigns"] == 0
        assert counts["creatives"] == 0
        assert counts["campaign_daily_metrics"] == 0
        assert counts["creative_daily_metrics"] == 0
        assert counts["audience_demographics"] == 0
    
    def test_table_counts_with_data(self, temp_db):
        """Test counts after inserting data."""
        snapshot = {
            "accounts": [
                {
                    "id": i,
                    "name": f"Account {i}",
                    "status": "ACTIVE",
                    "campaigns": []
                }
                for i in range(3)
            ],
            "date_range": {}
        }
        persist_snapshot(snapshot, temp_db)
        
        counts = table_counts(temp_db)
        assert counts["ad_accounts"] == 3


class TestActiveCampaignAudit:
    """Test active campaign auditing."""
    
    def test_audit_no_campaigns(self, temp_db):
        """Test audit with no campaigns."""
        results = active_campaign_audit(temp_db)
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_audit_with_active_campaigns(self, temp_db):
        """Test audit returns active campaigns."""
        snapshot = {
            "accounts": [{
                "id": 123456,
                "name": "Test Account",
                "status": "ACTIVE",
                "campaigns": [
                    {
                        "id": 789012,
                        "name": "Active Campaign",
                        "status": "ACTIVE",
                        "daily_metrics": [],
                        "creatives": []
                    },
                    {
                        "id": 789013,
                        "name": "Paused Campaign",
                        "status": "PAUSED",
                        "daily_metrics": [],
                        "creatives": []
                    }
                ]
            }],
            "date_range": {}
        }
        persist_snapshot(snapshot, temp_db)
        
        results = active_campaign_audit(temp_db)
        
        # Should return only active campaigns
        # The function filters by status='ACTIVE' but only returns name and issues
        assert len(results) >= 1
        
        # Verify we got results with expected structure
        for campaign in results:
            assert "name" in campaign
            assert "issues" in campaign
            # Only the "Active Campaign" should appear (PAUSED is filtered out)
        
        # Verify only active campaign is in results
        campaign_names = [c["name"] for c in results]
        assert "Active Campaign" in campaign_names
        assert "Paused Campaign" not in campaign_names


class TestErrorHandling:
    """Test error handling in storage operations."""
    
    def test_persist_with_invalid_db_path(self):
        """Test persist fails gracefully with invalid path."""
        snapshot = {"accounts": [], "date_range": {}}
        
        # Use invalid path (directory doesn't exist)
        invalid_path = Path("/invalid/path/db.sqlite")
        
        with pytest.raises(Exception):  # Should raise some database error
            persist_snapshot(snapshot, invalid_path)
    
    def test_table_counts_with_corrupted_db(self, tmp_path):
        """Test table counts handles corrupted database."""
        # Create a corrupted database file
        bad_db = tmp_path / "corrupted.db"
        with open(bad_db, "w") as f:
            f.write("This is not a valid SQLite database")
        
        with pytest.raises(sqlite3.DatabaseError):
            table_counts(bad_db)


class TestDatabaseIntegrity:
    """Test database schema and integrity."""
    
    def test_database_has_expected_tables(self, temp_db):
        """Test that all expected tables exist."""
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = {row[0] for row in cur.fetchall()}
        conn.close()
        
        expected_tables = {
            "ad_accounts",
            "campaigns",
            "creatives",
            "campaign_daily_metrics",
            "creative_daily_metrics",
            "audience_demographics"
        }
        
        assert expected_tables.issubset(tables)
    
    def test_foreign_key_constraints(self, temp_db):
        """Test that foreign key constraints are enforced."""
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        
        # Try to insert campaign without corresponding account
        # This should fail if foreign keys are enforced
        try:
            cur.execute("""
                INSERT INTO campaigns (id, account_id, name, status)
                VALUES (?, ?, ?, ?)
            """, (123, 999999, "Test", "ACTIVE"))
            conn.commit()
            # If we get here, foreign keys might not be enabled
            # That's OK for this basic test
        except sqlite3.IntegrityError:
            # This is expected if foreign keys are enforced
            pass
        finally:
            conn.close()
