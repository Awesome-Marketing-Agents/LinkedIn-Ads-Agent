"""Sync orchestration with SSE streaming via asyncio.Queue."""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import Any

from app.core.security import AuthManager
from app.crud.accounts import upsert_account
from app.crud.campaigns import upsert_campaign
from app.crud.demographics import upsert_demographics
from app.crud.metrics import upsert_campaign_daily_metrics, upsert_creatives
from app.linkedin.client import LinkedInClient
from app.linkedin.fetchers import fetch_ad_accounts, fetch_campaigns, fetch_creatives
from app.linkedin.metrics import (
    fetch_campaign_metrics,
    fetch_creative_metrics,
    fetch_demographics,
)
from app.services.snapshot import assemble_snapshot, save_snapshot_json
from app.utils.logging import get_logger, log_sync_progress

logger = get_logger(__name__)


class SyncJob:
    def __init__(self, job_id: str) -> None:
        self.id = job_id
        self.status: str = "running"
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.result: dict[str, Any] | None = None
        self.error: str | None = None

    def emit(self, step: str, detail: str) -> None:
        self.queue.put_nowait({"step": step, "detail": detail})
        log_sync_progress(step, 0)


# In-memory job store
_jobs: dict[str, SyncJob] = {}


def get_job(job_id: str) -> SyncJob | None:
    return _jobs.get(job_id)


def create_job(job_id: str) -> SyncJob:
    job = SyncJob(job_id)
    _jobs[job_id] = job
    return job


async def run_sync(job: SyncJob, get_session_fn: Any) -> None:
    """Run the full sync pipeline, emitting progress events."""
    try:
        auth = AuthManager()
        if not auth.is_authenticated():
            raise RuntimeError("Not authenticated. Run auth flow first.")

        client = LinkedInClient(auth)
        today = date.today()
        date_start = today - timedelta(days=90)

        job.emit("1/6", "Fetching ad accounts...")
        accounts = await fetch_ad_accounts(client)
        job.emit("1/6", f"Found {len(accounts)} account(s).")

        if not accounts:
            job.emit("done", "No ad accounts found.")
            job.status = "completed"
            return

        all_campaigns: list[dict] = []
        all_creatives: list[dict] = []
        all_campaign_ids: list[int] = []

        for account in accounts:
            account_id = account["id"]
            job.emit("2/6", f"Fetching campaigns for {account.get('name', account_id)}...")
            campaigns = await fetch_campaigns(client, account_id)
            for c in campaigns:
                c["_account_id"] = account_id
            all_campaigns.extend(campaigns)

            campaign_ids = [c["id"] for c in campaigns]
            all_campaign_ids.extend(campaign_ids)

            job.emit("3/6", f"Fetching creatives for {account.get('name', account_id)}...")
            creatives = await fetch_creatives(client, account_id, campaign_ids)
            all_creatives.extend(creatives)

        job.emit("2/6", f"Found {len(all_campaigns)} campaign(s) across {len(accounts)} account(s).")
        job.emit("3/6", f"Found {len(all_creatives)} creative(s).")
        job.emit("4-6/6", "Fetching metrics and demographics in parallel...")

        camp_metrics, creat_metrics, demographics = await asyncio.gather(
            fetch_campaign_metrics(client, all_campaign_ids, date_start, today),
            fetch_creative_metrics(client, all_campaign_ids, date_start, today),
            fetch_demographics(client, all_campaign_ids, date_start, today),
        )

        job.emit("4-6/6", f"{len(camp_metrics)} campaign metrics, {len(creat_metrics)} creative metrics.")

        job.emit("assemble", "Assembling snapshot...")
        snapshot = assemble_snapshot(
            accounts, all_campaigns, all_creatives,
            camp_metrics, creat_metrics, demographics,
            date_start, today,
        )

        json_path = save_snapshot_json(snapshot)
        job.emit("persist", f"JSON saved to {json_path}")

        # Persist to database
        job.emit("persist", "Updating database...")
        session_gen = get_session_fn()
        session = next(session_gen)
        try:
            for acct in snapshot.get("accounts", []):
                upsert_account(session, acct)
                for camp in acct.get("campaigns", []):
                    upsert_campaign(session, acct["id"], camp)
                    upsert_campaign_daily_metrics(session, camp)
                    upsert_creatives(session, acct["id"], camp)
                upsert_demographics(session, acct, snapshot.get("date_range", {}))
            session.commit()
        finally:
            try:
                next(session_gen)
            except StopIteration:
                pass

        job.emit("persist", "Database updated.")
        job.status = "completed"
        job.result = {"json_path": str(json_path), "account_count": len(accounts)}
        job.emit("done", "Sync complete!")

    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        job.emit("error", str(exc))
        logger.error("Sync failed: %s", exc, exc_info=True)
