import bootstrap  # noqa: F401  — adds src/ to sys.path

from flask import Flask, redirect, request, render_template_string, make_response, Response
from datetime import datetime, timedelta, timezone

from linkedin_action_center.auth.manager import AuthManager
from linkedin_action_center.core.config import OAUTH_STATE
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

app = Flask(__name__)
auth_manager = AuthManager()


LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LinkedIn Ads Action Center</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f4f4f9; color: #333; padding: 2rem; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #0077B5; margin-bottom: .5rem; }
        h2 { color: #0077B5; margin: 1.5rem 0 .5rem; }
        .subtitle { color: #666; margin-bottom: 2rem; }
        .card { background: #fff; border-radius: 8px; padding: 1.5rem;
                margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,.12); }
        .card h3 { margin-bottom: .5rem; }
        .card p  { color: #555; margin-bottom: .75rem; }
        a.btn { display: inline-block; padding: .6rem 1.2rem; border-radius: 6px;
                background: #0077B5; color: #fff; text-decoration: none; font-weight: 600; }
        a.btn:hover { background: #005f8f; }
        a.btn-secondary { background: #555; }
        a.btn-secondary:hover { background: #333; }
        pre { background: #1e1e2e; color: #cdd6f4; padding: 1rem; border-radius: 6px;
              overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
        .badge { display: inline-block; padding: .25rem .6rem; border-radius: 12px;
                 font-size: .85rem; font-weight: 600; }
        .badge-ok  { background: #d4edda; color: #155724; }
        .badge-warn{ background: #fff3cd; color: #856404; }
        .badge-err { background: #f8d7da; color: #721c24; }
        nav { margin-bottom: 2rem; }
        nav a { margin-right: 1rem; color: #0077B5; text-decoration: none; font-weight: 600; }
        nav a:hover { text-decoration: underline; }
    </style>
</head>
<body>
<div class="container">
    <h1>LinkedIn Ads Action Center</h1>
    {{ content|safe }}
</div>
</body>
</html>
"""


def _render(content_html: str) -> Response:
    response = make_response(render_template_string(LAYOUT, content=content_html))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response



@app.route("/")
def home():
    cards = """
    <div class="card">
        <h3>1. Authenticate</h3>
        <p>Connect your LinkedIn account. If you are already authenticated the status page will confirm it.</p>
        <a class="btn" href="/auth">Authenticate &rarr;</a>
    </div>
    <div class="card">
        <h3>2. Sync Data</h3>
        <p>Pull ad accounts, campaigns, creatives and performance metrics from the LinkedIn API.</p>
        <a class="btn" href="/sync">Sync Now &rarr;</a>
    </div>
    <div class="card">
        <h3>3. Check Status</h3>
        <p>View token health, database row counts, and active‑campaign audit results.</p>
        <a class="btn btn-secondary" href="/status">View Status &rarr;</a>
    </div>
    """
    return _render(cards)


@app.route("/auth")
def auth():
    """If already authenticated, show confirmation. Otherwise redirect to LinkedIn."""
    if auth_manager.is_authenticated():
        status = auth_manager.token_status()
        badge = "badge-ok" if not status["access_token_expired"] else "badge-err"
        html = f"""
        <div class="card">
            <h3>Already Authenticated <span class="badge {badge}">Active</span></h3>
            <p>Access token: <strong>{status['access_token_days_remaining']} days remaining</strong></p>
            <p>Refresh token: <strong>{status.get('refresh_token_days_remaining', 'N/A')} days remaining</strong></p>
            <p>Last saved: {status.get('saved_at', 'unknown')}</p>
            <br><a class="btn btn-secondary" href="/">Home</a>
        </div>
        """
        return _render(html)

    # Not authenticated — redirect browser to LinkedIn
    auth_url = auth_manager.get_authorization_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """LinkedIn redirects here after the user approves access."""
    # Verify state
    state = request.args.get("state")
    if state != OAUTH_STATE:
        return _render('<div class="card"><h3 class="badge badge-err">Error</h3><p>Invalid state parameter — possible CSRF attack.</p></div>'), 400

    error = request.args.get("error")
    if error:
        desc = request.args.get("error_description", "")
        return _render(f'<div class="card"><h3 class="badge badge-err">OAuth Error</h3><p>{error}: {desc}</p></div>'), 400

    code = request.args.get("code")
    if not code:
        return _render('<div class="card"><h3 class="badge badge-err">Error</h3><p>No authorization code received.</p></div>'), 400

    try:
        auth_manager.exchange_code_for_token(code)
    except Exception as exc:
        return _render(f'<div class="card"><h3 class="badge badge-err">Token Exchange Failed</h3><pre>{exc}</pre></div>'), 500

    status = auth_manager.token_status()
    html = f"""
    <div class="card">
        <h3>Authentication Successful! <span class="badge badge-ok">Connected</span></h3>
        <p>Access token: <strong>{status['access_token_days_remaining']} days remaining</strong></p>
        <p>Refresh token: <strong>{status.get('refresh_token_days_remaining', 'N/A')} days remaining</strong></p>
        <br><a class="btn" href="/">Go to Dashboard</a>
    </div>
    """
    return _render(html)


@app.route("/sync")
def sync():
    """Run the full data sync and show results."""
    if not auth_manager.is_authenticated():
        return _render('<div class="card"><h3 class="badge badge-warn">Not Authenticated</h3>'
                       '<p>Please <a href="/auth">authenticate</a> first.</p></div>'), 401

    logs: list[str] = []
    try:
        client = LinkedInClient(auth_manager)
        today = datetime.now(tz=timezone.utc).date()
        date_start = today - timedelta(days=90)
        logs.append(f"Date range: {date_start} → {today}  ({(today - date_start).days} days)")

        # Fetch entities
        accounts = fetch_ad_accounts(client)
        logs.append(f"Ad accounts: {len(accounts)}")

        all_campaigns, all_creatives = [], []
        for acct in accounts:
            acct_id = acct["id"]
            camps = fetch_campaigns(client, acct_id)
            all_campaigns.extend(camps)
            logs.append(f"  Account {acct_id}: {len(camps)} campaigns")
            campaign_ids = [c["id"] for c in camps]
            crs = fetch_creatives(client, acct_id, campaign_ids)
            all_creatives.extend(crs)
            logs.append(f"  Account {acct_id}: {len(crs)} creatives")

        # Fetch metrics
        camp_metrics = fetch_campaign_metrics(client, [c["id"] for c in all_campaigns], date_start, today)
        logs.append(f"Campaign metric rows: {len(camp_metrics)}")

        creative_metrics = fetch_creative_metrics(client, [c["id"] for c in all_campaigns], date_start, today)
        logs.append(f"Creative metric rows: {len(creative_metrics)}")

        demographics = fetch_demographics(client, [c["id"] for c in all_campaigns], date_start, today)
        logs.append(f"Demographic rows: {len(demographics)}")

        # Persist
        snapshot = assemble_snapshot(accounts, all_campaigns, all_creatives,
                                     camp_metrics, creative_metrics, demographics,
                                     date_start, today)
        save_snapshot_json(snapshot)
        persist_snapshot(snapshot)
        logs.append("Snapshot saved to JSON and SQLite.")
    except Exception as exc:
        logs.append(f"\nERROR: {exc}")

    pre = "\n".join(logs)
    html = f'<h2>Sync Results</h2><pre>{pre}</pre><br><a class="btn btn-secondary" href="/">Home</a>'
    return _render(html)


@app.route("/status")
def status():
    """Show token health and database statistics."""
    lines: list[str] = []

    # Token info
    ts = auth_manager.token_status()
    if ts.get("authenticated"):
        lines.append("Token        : VALID")
        lines.append(f"Access token : {ts['access_token_days_remaining']} days remaining")
        rt = ts.get("refresh_token_days_remaining")
        if rt is not None:
            lines.append(f"Refresh token: {rt} days remaining")
        lines.append(f"Last saved   : {ts.get('saved_at', 'N/A')}")
    else:
        lines.append("Token        : NOT AUTHENTICATED")
        lines.append(f"Reason       : {ts.get('reason', 'unknown')}")

    # DB counts
    lines.append("")
    try:
        counts = table_counts()
        lines.append("Database row counts:")
        for tbl, cnt in counts.items():
            lines.append(f"  {tbl:30s} {cnt}")
    except Exception as exc:
        lines.append(f"Database error: {exc}")

    # Audit
    try:
        audit = active_campaign_audit()
        if audit:
            lines.append(f"\nActive campaigns (last audit): {len(audit)}")
    except Exception:
        pass

    badge = "badge-ok" if ts.get("authenticated") else "badge-err"
    label = "Healthy" if ts.get("authenticated") else "Action Required"
    pre = "\n".join(lines)
    html = (f'<h2>System Status <span class="badge {badge}">{label}</span></h2>'
            f'<pre>{pre}</pre><br><a class="btn btn-secondary" href="/">Home</a>')
    return _render(html)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
