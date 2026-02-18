"""LinkedIn Ads Action Center -- CLI entry point.

Usage
-----
    python main.py auth        Run the OAuth flow (or verify existing tokens)
    python main.py sync        Pull all data from LinkedIn and persist locally
    python main.py status      Print token and database health summary
"""

from __future__ import annotations

import os
import sys

import bootstrap

from datetime import datetime, timedelta, timezone

from linkedin_action_center.auth.manager import AuthManager
from linkedin_action_center.ingestion.client import LinkedInClient
from linkedin_action_center.ingestion.fetchers import (
    fetch_ad_accounts,
    fetch_campaigns,
    fetch_creatives,
)
from linkedin_action_center.ingestion.metrics import (
    fetch_campaign_metrics,
    fetch_creative_metrics,
    fetch_demographics,
)
from linkedin_action_center.storage.snapshot import assemble_snapshot, save_snapshot_json
from linkedin_action_center.storage.repository import (
    persist_snapshot,
    table_counts,
    active_campaign_audit,
)

# Ensure the `src` directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, 'src')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def cmd_auth() -> None:
    """Authenticate or verify existing tokens."""
    auth = AuthManager()
    if auth.is_authenticated():
        print("Already authenticated.")
        auth.check_token_health()
    else:
        print("No valid token found.")
        print("Visit this URL to authorise the application:\n")
        print(f"  {auth.get_authorization_url()}\n")
        print("After authorising, paste the ?code= value from the redirect URL:")
        code = input("  code> ").strip()
        auth.exchange_code_for_token(code)
        print("Authentication complete.")

    status = auth.token_status()
    print(f"\nAccess token  : {'valid' if not status['access_token_expired'] else 'EXPIRED'}"
          f" ({status['access_token_days_remaining']} days remaining)")
    rt = status.get("refresh_token_days_remaining")
    if rt is not None:
        print(f"Refresh token : {rt} days remaining")


def cmd_sync() -> None:
    """Pull all data from LinkedIn and persist to JSON + SQLite."""
    auth = AuthManager()
    if not auth.is_authenticated():
        print("Not authenticated. Run 'python main.py auth' first.")
        sys.exit(1)

    client = LinkedInClient(auth)

    today = datetime.now(tz=timezone.utc).date()
    date_start = today - timedelta(days=90)

    # 1. Fetch entities
    print(f"Date range: {date_start} -> {today} ({(today - date_start).days} days)\n")

    print("[1/6] Fetching ad accounts...")
    accounts = fetch_ad_accounts(client)
    print(f"      Found {len(accounts)} account(s).\n")

    if not accounts:
        print("No ad accounts found. Nothing to sync.")
        return

    account_id = accounts[0]["id"]

    print("[2/6] Fetching campaigns...")
    campaigns = fetch_campaigns(client, account_id)
    print(f"      Found {len(campaigns)} campaign(s).\n")

    campaign_ids = [c["id"] for c in campaigns]

    print("[3/6] Fetching creatives...")
    creatives = fetch_creatives(client, account_id, campaign_ids)
    print(f"      Found {len(creatives)} creative(s).\n")

    # 2. Fetch metrics
    print("[4/6] Fetching campaign metrics (daily, 90 days)...")
    camp_metrics = fetch_campaign_metrics(client, campaign_ids, date_start, today)
    print(f"      {len(camp_metrics)} metric rows.\n")

    print("[5/6] Fetching creative metrics (daily, 90 days)...")
    creat_metrics = fetch_creative_metrics(client, campaign_ids, date_start, today)
    print(f"      {len(creat_metrics)} metric rows.\n")

    print("[6/6] Fetching audience demographics...")
    demographics = fetch_demographics(client, campaign_ids, date_start, today)
    total_demo = sum(len(v) for v in demographics.values())
    print(f"      {total_demo} demographic segments across {len(demographics)} pivots.\n")

    # 3. Assemble and persist
    print("Assembling snapshot...")
    snapshot = assemble_snapshot(
        accounts, campaigns, creatives,
        camp_metrics, creat_metrics, demographics,
        date_start, today,
    )

    json_path = save_snapshot_json(snapshot)
    size_kb = json_path.stat().st_size / 1024
    print(f"  JSON  -> {json_path} ({size_kb:.1f} KB)")

    persist_snapshot(snapshot)
    from linkedin_action_center.core.config import DATABASE_FILE
    db_size = DATABASE_FILE.stat().st_size / 1024
    print(f"  SQLite -> {DATABASE_FILE} ({db_size:.1f} KB)")

    print("\nSync complete.")


def cmd_status() -> None:
    """Print token health and database row counts."""
    auth = AuthManager()
    status = auth.token_status()

    print("-- Token Status " + "-" * 48)
    if status["authenticated"]:
        print("  Authenticated  : yes")
        print(f"  Access token   : {status['access_token_days_remaining']} days remaining")
        rt = status.get("refresh_token_days_remaining")
        if rt is not None:
            print(f"  Refresh token  : {rt} days remaining")
        print(f"  Last saved     : {status.get('saved_at', 'N/A')}")
    else:
        print(f"  Authenticated  : no ({status.get('reason', 'token expired or missing')})")

    print()
    print("-- Database " + "-" * 52)
    try:
        counts = table_counts()
        for table, count in counts.items():
            print(f"  {table:30s}: {count:>6} rows")
    except Exception as exc:
        print(f"  Could not read database: {exc}")

    print()
    print("-- Active Campaign Audit " + "-" * 40)
    try:
        audit = active_campaign_audit()
        if not audit:
            print("  No active campaigns found.")
        for entry in audit:
            if entry["issues"]:
                print(f"  {entry['name']}: {', '.join(entry['issues'])}")
            else:
                print(f"  {entry['name']}: no issues detected")
    except Exception:
        print("  (no data yet)")


COMMANDS = {
    "auth": cmd_auth,
    "sync": cmd_sync,
    "status": cmd_status,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0)
    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
