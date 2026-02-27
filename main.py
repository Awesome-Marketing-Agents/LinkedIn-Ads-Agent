import bootstrap  # noqa: F401  — adds src/ to sys.path

import json
from html import escape as _h
from pathlib import Path
from flask import Flask, redirect, request, render_template_string, make_response, Response
from datetime import datetime, timedelta, timezone

from linkedin_action_center.auth.manager import AuthManager
from linkedin_action_center.core.config import OAUTH_STATE
from linkedin_action_center.core.config import SNAPSHOT_DIR
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
        .container { max-width: 1100px; margin: 0 auto; }
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
        .muted { color: #666; font-size: .95rem; }
        .warnbox { border: 1px solid #ffeeba; background: #fff3cd; color: #856404; padding: .75rem; border-radius: 8px; margin-bottom: 1rem; }
        .errbox { border: 1px solid #f5c6cb; background: #f8d7da; color: #721c24; padding: .75rem; border-radius: 8px; margin-bottom: 1rem; }
        form.inline { display: flex; flex-wrap: wrap; gap: .75rem; align-items: end; }
        label { font-weight: 600; color: #333; display: block; margin-bottom: .25rem; }
        select, input { padding: .5rem .6rem; border: 1px solid #ddd; border-radius: 6px; min-width: 180px; background: #fff; }
        input[type=number] { min-width: 120px; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.12); }
        thead th { position: sticky; top: 0; background: #f1f5f9; text-align: left; font-size: .9rem; padding: .6rem .7rem; border-bottom: 1px solid #e5e7eb; }
        tbody td { padding: .55rem .7rem; border-bottom: 1px solid #f0f0f0; font-size: .92rem; vertical-align: top; }
        tbody tr:hover { background: #f8fafc; }
        .right { text-align: right; font-variant-numeric: tabular-nums; }
        .nowrap { white-space: nowrap; }
        .pager { margin-top: 1rem; display: flex; gap: .75rem; align-items: center; flex-wrap: wrap; }
    </style>
</head>
<body>
<div class="container">
    <h1>LinkedIn Ads Action Center</h1>
    <nav>
      <a href="/">Home</a>
      <a href="/auth">Auth</a>
      <a href="/sync">Sync</a>
      <a href="/report">Report</a>
      <a href="/status">Status</a>
    </nav>
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
        <h3>3. Explore Report Data</h3>
        <p>View the latest snapshot in a clean table (campaign daily, campaign summary, creative summary).</p>
        <a class="btn btn-secondary" href="/report">Open Report &rarr;</a>
    </div>
    <div class="card">
        <h3>4. Check Status</h3>
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

        all_campaigns: list[dict] = []
        all_creatives: list[dict] = []
        demographics_by_account: dict[int, dict[str, list[dict]]] = {}
        for acct in accounts:
            acct_id = acct["id"]
            camps = fetch_campaigns(client, acct_id)
            for c in camps:
                c["_account_id"] = acct_id
            all_campaigns.extend(camps)
            logs.append(f"  Account {acct_id}: {len(camps)} campaigns")
            campaign_ids = [c["id"] for c in camps]
            crs = fetch_creatives(client, acct_id, campaign_ids)
            for cr in crs:
                cr["_account_id"] = acct_id
            all_creatives.extend(crs)
            logs.append(f"  Account {acct_id}: {len(crs)} creatives")
            demo = fetch_demographics(client, campaign_ids, date_start, today)
            demographics_by_account[acct_id] = demo
            logs.append(f"  Account {acct_id}: demographics pivots {len(demo)}")

        # Fetch metrics
        camp_metrics = fetch_campaign_metrics(client, [c["id"] for c in all_campaigns], date_start, today)
        logs.append(f"Campaign metric rows: {len(camp_metrics)}")

        creative_metrics = fetch_creative_metrics(client, [c["id"] for c in all_campaigns], date_start, today)
        logs.append(f"Creative metric rows: {len(creative_metrics)}")

        # Persist
        snapshot = assemble_snapshot(accounts, all_campaigns, all_creatives,
                                     camp_metrics, creative_metrics, demographics_by_account,
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


def _latest_snapshot_path() -> Path | None:
    if not SNAPSHOT_DIR.exists():
        return None
    snaps = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return snaps[0] if snaps else None


def _fmt_num(v, decimals: int = 0) -> str:
    if v is None:
        return ""
    try:
        if decimals == 0:
            return f"{int(v):,}"
        return f"{float(v):,.{decimals}f}"
    except Exception:
        return str(v)


def _fmt_pct(v, decimals: int = 2) -> str:
    if v is None:
        return ""
    try:
        return f"{float(v):.{decimals}f}%"
    except Exception:
        return str(v)


def _extract_id(urn: str | None) -> str:
    if not urn:
        return ""
    s = str(urn)
    return s.split(":")[-1] if ":" in s else s


def _fmt_utc_ms(ms: int | float | None) -> str:
    if ms is None:
        return ""
    try:
        dt = datetime.fromtimestamp(float(ms) / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ms)


def _flatten_campaign_daily(snapshot: dict) -> list[dict]:
    out: list[dict] = []
    for acct in snapshot.get("accounts", []):
        acct_name = acct.get("name", "")
        currency = acct.get("currency", "")
        for camp in acct.get("campaigns", []):
            settings = camp.get("settings", {}) or {}
            camp_group = settings.get("campaign_group")
            run_schedule = settings.get("run_schedule", {}) or {}
            camp_start_ms = run_schedule.get("start")
            for d in camp.get("daily_metrics", []) or []:
                impressions = d.get("impressions", 0) or 0
                clicks = d.get("clicks", 0) or 0
                spend = d.get("spend", 0.0) or 0.0
                likes = d.get("likes", 0) or 0
                comments = d.get("comments", 0) or 0
                shares = d.get("shares", 0) or 0
                follows = d.get("follows", 0) or 0
                leads = d.get("leads", 0) or 0
                social_actions = likes + comments + shares + follows
                engagements = clicks + social_actions
                cpm = (float(spend) / impressions * 1000.0) if impressions else 0.0
                engagement_rate = (engagements / impressions * 100.0) if impressions else 0.0
                conversions = d.get("conversions", 0) or 0
                cpc = d.get("cpc", 0.0) or 0.0
                ctr = d.get("ctr", 0.0) or 0.0
                cpa = (float(spend) / conversions) if conversions else 0.0
                out.append({
                    "Start Date (in UTC)": d.get("date", ""),
                    "Account Name": acct_name,
                    "Currency": currency,
                    "Campaign Group ID": _extract_id(camp_group),
                    "Campaign ID": camp.get("id", ""),
                    "Campaign Name": camp.get("name", ""),
                    "Campaign Type": camp.get("type", ""),
                    "Campaign Status": camp.get("status", ""),
                    "Cost Type": settings.get("cost_type", ""),
                    "Daily Budget": settings.get("daily_budget", ""),
                    "Campaign Start Date": _fmt_utc_ms(camp_start_ms),
                    "Total Spent": spend,
                    "Impressions": impressions,
                    "Clicks": clicks,
                    "Click Through Rate": ctr,
                    "Average CPM": cpm,
                    "Average CPC": cpc,
                    "Reactions": likes,
                    "Comments": comments,
                    "Shares": shares,
                    "Follows": follows,
                    "Leads": leads,
                    "Clicks to Landing Page": d.get("landing_page_clicks", 0) or 0,
                    "Conversions": conversions,
                    "Cost per Conversion": cpa,
                    "Total Social Actions": social_actions,
                    "Total Engagements": engagements,
                    "Engagement Rate": engagement_rate,
                })
    return out


def _flatten_campaign_summary(snapshot: dict) -> list[dict]:
    out: list[dict] = []
    for acct in snapshot.get("accounts", []):
        acct_name = acct.get("name", "")
        currency = acct.get("currency", "")
        for camp in acct.get("campaigns", []):
            settings = camp.get("settings", {}) or {}
            camp_group = settings.get("campaign_group")
            run_schedule = settings.get("run_schedule", {}) or {}
            camp_start_ms = run_schedule.get("start")
            ms = camp.get("metrics_summary", {}) or {}
            impressions = ms.get("impressions", 0) or 0
            clicks = ms.get("clicks", 0) or 0
            spend = ms.get("spend", 0.0) or 0.0
            likes = ms.get("likes", 0) or 0
            comments = ms.get("comments", 0) or 0
            shares = ms.get("shares", 0) or 0
            follows = ms.get("follows", 0) or 0
            leads = ms.get("leads", 0) or 0
            conversions = ms.get("conversions", 0) or 0
            social_actions = likes + comments + shares + follows
            engagements = clicks + social_actions
            engagement_rate = (engagements / impressions * 100.0) if impressions else 0.0
            cpa = (float(spend) / conversions) if conversions else 0.0
            out.append({
                "Account Name": acct_name,
                "Currency": currency,
                "Campaign Group ID": _extract_id(camp_group),
                "Campaign ID": camp.get("id", ""),
                "Campaign Name": camp.get("name", ""),
                "Campaign Type": camp.get("type", ""),
                "Campaign Status": camp.get("status", ""),
                "Cost Type": settings.get("cost_type", ""),
                "Daily Budget": settings.get("daily_budget", ""),
                "Campaign Start Date": _fmt_utc_ms(camp_start_ms),
                "Total Spent": spend,
                "Impressions": impressions,
                "Clicks": clicks,
                "Click Through Rate": ms.get("ctr", 0.0) or 0.0,
                "Average CPM": ms.get("cpm", 0.0) or 0.0,
                "Average CPC": ms.get("cpc", 0.0) or 0.0,
                "Reactions": likes,
                "Comments": comments,
                "Shares": shares,
                "Follows": follows,
                "Leads": leads,
                "Clicks to Landing Page": ms.get("landing_page_clicks", 0) or 0,
                "Conversions": conversions,
                "Cost per Conversion": cpa,
                "Total Social Actions": social_actions,
                "Total Engagements": engagements,
                "Engagement Rate": engagement_rate,
            })
    return out


def _flatten_creative_summary(snapshot: dict) -> list[dict]:
    out: list[dict] = []
    for acct in snapshot.get("accounts", []):
        acct_name = acct.get("name", "")
        currency = acct.get("currency", "")
        for camp in acct.get("campaigns", []):
            for cr in camp.get("creatives", []) or []:
                ms = cr.get("metrics_summary", {}) or {}
                out.append({
                    "Account Name": acct_name,
                    "Currency": currency,
                    "Campaign ID": camp.get("id", ""),
                    "Campaign Name": camp.get("name", ""),
                    "Creative ID": _extract_id(cr.get("id")),
                    "Creative Intended Status": cr.get("intended_status", ""),
                    "Creative Is Serving": cr.get("is_serving", False),
                    "Serving Hold Reasons": ", ".join([str(x) for x in (cr.get("serving_hold_reasons") or [])])[:200],
                    "Content Reference": cr.get("content_reference", ""),
                    "Total Spent": ms.get("spend", 0.0) or 0.0,
                    "Impressions": ms.get("impressions", 0) or 0,
                    "Clicks": ms.get("clicks", 0) or 0,
                    "Click Through Rate": ms.get("ctr", 0.0) or 0.0,
                    "Average CPM": ms.get("cpm", 0.0) or 0.0,
                    "Average CPC": ms.get("cpc", 0.0) or 0.0,
                    "Reactions": ms.get("likes", 0) or 0,
                    "Comments": ms.get("comments", 0) or 0,
                    "Shares": ms.get("shares", 0) or 0,
                    "Follows": ms.get("follows", 0) or 0,
                    "Leads": ms.get("leads", 0) or 0,
                    "Conversions": ms.get("conversions", 0) or 0,
                })
    return out


def _render_table(rows: list[dict], columns: list[str], page: int, page_size: int) -> str:
    total = len(rows)
    page_size = max(10, min(page_size, 500))
    max_page = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, max_page))
    start = (page - 1) * page_size
    end = min(total, start + page_size)

    def cell(col: str, v) -> str:
        cls = []
        if col in {"Impressions","Clicks","Reactions","Comments","Shares","Follows","Leads","Conversions","Clicks to Landing Page"}:
            cls.append("right")
            txt = _fmt_num(v, 0)
        elif col in {"Total Spent","Average CPM","Average CPC","Cost per Conversion","Daily Budget"}:
            cls.append("right")
            txt = _fmt_num(v, 2)
        elif col in {"Click Through Rate","Engagement Rate"}:
            cls.append("right")
            txt = _fmt_pct(v, 2)
        else:
            txt = "" if v is None else str(v)
        if col in {"Start Date (in UTC)","Campaign Start Date"}:
            cls.append("nowrap")
        return f'<td class=\"{" ".join(cls)}\">{_h(txt)}</td>'

    thead = "<thead><tr>" + "".join(f"<th>{_h(c)}</th>" for c in columns) + "</tr></thead>"
    body_rows = []
    for r in rows[start:end]:
        body_rows.append("<tr>" + "".join(cell(c, r.get(c)) for c in columns) + "</tr>")
    tbody = "<tbody>" + "".join(body_rows) + "</tbody>"
    table = f"<table>{thead}{tbody}</table>"
    pager = (
        f'<div class=\"pager\">'
        f'<div class=\"muted\">Rows {start+1:,}-{end:,} of {total:,} | Page {page} of {max_page}</div>'
        f'<a class=\"btn btn-secondary\" href=\"?page={max(1,page-1)}&page_size={page_size}\">Prev</a>'
        f'<a class=\"btn btn-secondary\" href=\"?page={min(max_page,page+1)}&page_size={page_size}\">Next</a>'
        f'</div>'
    )
    return table + pager


@app.route("/report")
def report():
    snap_path = _latest_snapshot_path()
    if not snap_path:
        return _render('<div class="card"><h3>No snapshot found</h3><p>Run <a href="/sync">Sync</a> first.</p></div>')

    mode = request.args.get("mode", "campaign_daily")
    page = int(request.args.get("page", "1") or "1")
    page_size = int(request.args.get("page_size", "50") or "50")

    snapshot = json.loads(Path(snap_path).read_text(encoding="utf-8"))

    # Detect duplicated campaigns across accounts (a known bug in older snapshots)
    campaign_to_accounts: dict[str, set] = {}
    for acct in snapshot.get("accounts", []):
        aid = str(acct.get("id"))
        for camp in acct.get("campaigns", []) or []:
            cid = str(camp.get("id"))
            campaign_to_accounts.setdefault(cid, set()).add(aid)
    duplicated = sorted([cid for cid, aids in campaign_to_accounts.items() if len(aids) > 1])

    warn_html = ""
    if duplicated:
        warn_html = (
            '<div class="warnbox"><strong>Warning:</strong> This snapshot appears to have the same campaign IDs '
            'under multiple accounts. That usually means the snapshot was assembled with an older bug. '
            'After updating code, run <a href="/sync">Sync</a> again to generate a corrected snapshot.</div>'
        )

    options = {
        "campaign_daily": "Campaign Daily (time series)",
        "campaign_summary": "Campaign Summary (90d total)",
        "creative_summary": "Creative Summary (90d total)",
    }
    mode_label = options.get(mode, options["campaign_daily"])

    if mode == "campaign_summary":
        rows = _flatten_campaign_summary(snapshot)
        columns = [
            "Account Name","Currency","Campaign Group ID","Campaign ID","Campaign Name","Campaign Type","Campaign Status",
            "Cost Type","Daily Budget","Campaign Start Date",
            "Total Spent","Impressions","Clicks","Click Through Rate","Average CPM","Average CPC",
            "Reactions","Comments","Shares","Follows","Leads","Clicks to Landing Page","Conversions","Cost per Conversion",
            "Total Social Actions","Total Engagements","Engagement Rate",
        ]
    elif mode == "creative_summary":
        rows = _flatten_creative_summary(snapshot)
        columns = [
            "Account Name","Currency","Campaign ID","Campaign Name",
            "Creative ID","Creative Intended Status","Creative Is Serving","Serving Hold Reasons","Content Reference",
            "Total Spent","Impressions","Clicks","Click Through Rate","Average CPM","Average CPC",
            "Reactions","Comments","Shares","Follows","Leads","Conversions",
        ]
    else:
        rows = _flatten_campaign_daily(snapshot)
        columns = [
            "Start Date (in UTC)","Account Name","Currency","Campaign Group ID","Campaign ID","Campaign Name","Campaign Type","Campaign Status",
            "Cost Type","Daily Budget","Campaign Start Date",
            "Total Spent","Impressions","Clicks","Click Through Rate","Average CPM","Average CPC",
            "Reactions","Comments","Shares","Follows","Leads","Clicks to Landing Page","Conversions","Cost per Conversion",
            "Total Social Actions","Total Engagements","Engagement Rate",
        ]

    rows.sort(key=lambda r: (r.get("Account Name",""), r.get("Campaign Name",""), r.get("Start Date (in UTC)","")))

    form = (
        f'<div class="card">'
        f'<h3>Report</h3>'
        f'<p class="muted">Snapshot: <code>{_h(str(snap_path.name))}</code> • View: <strong>{_h(mode_label)}</strong></p>'
        f'{warn_html}'
        f'<form class="inline" method="get">'
        f'  <div><label for="mode">View</label><select name="mode" id="mode">'
        + "".join([f'<option value="{k}" {"selected" if k==mode else ""}>{_h(v)}</option>' for k,v in options.items()])
        + f'</select></div>'
        f'  <div><label for="page_size">Page size</label><input type="number" min="10" max="500" name="page_size" id="page_size" value="{page_size}"></div>'
        f'  <div><button class="btn" type="submit">Apply</button></div>'
        f'</form>'
        f'</div>'
    )

    table_html = _render_table(rows, columns, page=page, page_size=page_size)
    return _render("<h2>Report</h2>" + form + table_html)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
