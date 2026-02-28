"""
UI layer — layout template, rendering helpers, and all Flask routes.
Separated from main.py so the entry point stays lean.
"""

import json
from html import escape as _h
from pathlib import Path
from flask import redirect, request, render_template_string, make_response, Response
from datetime import datetime, timedelta, timezone

from linkedin_action_center.auth.manager import AuthManager
from linkedin_action_center.core.config import OAUTH_STATE, SNAPSHOT_DIR
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
    resolve_demographic_urns,
)
from linkedin_action_center.storage.snapshot import assemble_snapshot, save_snapshot_json
from linkedin_action_center.storage.repository import (
    persist_snapshot,
    table_counts,
    active_campaign_audit,
)


# ---------------------------------------------------------------------------
# Layout template
# ---------------------------------------------------------------------------

LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LinkedIn Ads Action Center</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --ink:          #1a2332;
            --ink-secondary:#4a5568;
            --ink-tertiary: #718096;
            --ink-muted:    #a0aec0;
            --paper:        #f8f7f4;
            --paper-raised: #ffffff;
            --paper-inset:  #f0efe9;

            --sidebar-bg:   #1a2332;
            --sidebar-ink:  #cbd5e0;
            --sidebar-hover:#243044;
            --sidebar-active:#2d3b50;

            --border:       rgba(26,35,50,.10);
            --border-soft:  rgba(26,35,50,.06);
            --border-strong:rgba(26,35,50,.18);

            --brand:        #2b6cb0;
            --brand-hover:  #225591;
            --brand-subtle: rgba(43,108,176,.08);

            --healthy:      #2d8a6e;
            --healthy-bg:   rgba(45,138,110,.08);
            --warning:      #d4940a;
            --warning-bg:   rgba(212,148,10,.08);
            --danger:       #c4483e;
            --danger-bg:    rgba(196,72,62,.08);

            --sp-1: 4px; --sp-2: 8px; --sp-3: 12px; --sp-4: 16px;
            --sp-5: 20px; --sp-6: 24px; --sp-8: 32px; --sp-10: 40px;

            --radius-sm: 4px;
            --radius-md: 6px;
            --radius-lg: 8px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--paper);
            color: var(--ink);
            font-size: 14px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        .shell { display: flex; min-height: 100vh; }

        /* — sidebar — */
        .sidebar {
            width: 220px;
            flex-shrink: 0;
            background: var(--sidebar-bg);
            border-right: 1px solid rgba(255,255,255,.06);
            padding: var(--sp-6) 0;
            position: fixed;
            top: 0; left: 0; bottom: 0;
            overflow-y: auto;
        }
        .sidebar-brand {
            padding: 0 var(--sp-6) var(--sp-6);
            border-bottom: 1px solid rgba(255,255,255,.08);
            margin-bottom: var(--sp-4);
        }
        .sidebar-brand h1 {
            font-size: 13px; font-weight: 700; color: #fff;
            letter-spacing: -.01em; line-height: 1.3;
        }
        .sidebar-brand span {
            font-size: 11px; font-weight: 400; color: var(--ink-muted);
            letter-spacing: .02em; text-transform: uppercase;
        }
        .sidebar nav { display: flex; flex-direction: column; gap: var(--sp-1); padding: 0 var(--sp-2); }
        .sidebar nav a {
            display: flex; align-items: center; gap: var(--sp-3);
            padding: var(--sp-2) var(--sp-4);
            border-radius: var(--radius-md);
            color: var(--sidebar-ink);
            text-decoration: none;
            font-size: 13px; font-weight: 500;
            transition: background .12s ease, color .12s ease;
        }
        .sidebar nav a:hover { background: var(--sidebar-hover); color: #fff; }
        .sidebar nav a.active { background: var(--sidebar-active); color: #fff; }
        .sidebar nav a svg { width: 16px; height: 16px; opacity: .7; flex-shrink: 0; }
        .sidebar nav a:hover svg, .sidebar nav a.active svg { opacity: 1; }
        .sidebar-section {
            font-size: 10px; font-weight: 600; text-transform: uppercase;
            letter-spacing: .08em; color: var(--ink-muted);
            padding: var(--sp-5) var(--sp-6) var(--sp-2);
        }

        /* — main area — */
        .main { margin-left: 220px; flex: 1; min-width: 0; }
        .topbar {
            height: 52px;
            border-bottom: 1px solid var(--border);
            background: var(--paper-raised);
            display: flex; align-items: center;
            padding: 0 var(--sp-8);
            position: sticky; top: 0; z-index: 100;
        }
        .topbar h2 { font-size: 14px; font-weight: 600; color: var(--ink); letter-spacing: -.01em; }
        .topbar .badge { margin-left: var(--sp-3); }
        .content { padding: var(--sp-8); max-width: 1400px; }

        /* — typography — */
        h2 { font-size: 14px; font-weight: 600; color: var(--ink); letter-spacing: -.01em; }
        h3 { font-size: 13px; font-weight: 600; color: var(--ink); letter-spacing: -.005em; }
        p  { color: var(--ink-secondary); font-size: 13px; line-height: 1.55; }

        /* — cards — */
        .card {
            background: var(--paper-raised);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: var(--sp-6);
            margin-bottom: var(--sp-4);
        }
        .card h3 { margin-bottom: var(--sp-2); }
        .card p  { margin-bottom: var(--sp-3); }

        /* — action grid — */
        .action-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: var(--sp-4);
        }
        .action-card {
            background: var(--paper-raised);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: var(--sp-6);
            transition: border-color .15s ease;
        }
        .action-card:hover { border-color: var(--border-strong); }
        .action-card .step-num {
            display: inline-flex; align-items: center; justify-content: center;
            width: 24px; height: 24px; border-radius: 50%;
            background: var(--brand-subtle); color: var(--brand);
            font-size: 12px; font-weight: 600;
            margin-bottom: var(--sp-3);
        }
        .action-card h3 { margin-bottom: var(--sp-1); }
        .action-card p  { font-size: 12.5px; margin-bottom: var(--sp-4); }

        /* — buttons — */
        a.btn, button.btn {
            display: inline-flex; align-items: center; gap: var(--sp-2);
            padding: var(--sp-2) var(--sp-4);
            border-radius: var(--radius-md);
            background: var(--brand); color: #fff;
            text-decoration: none; font-family: inherit;
            font-size: 12.5px; font-weight: 600;
            border: none; cursor: pointer;
            transition: background .12s ease;
        }
        a.btn:hover, button.btn:hover { background: var(--brand-hover); }
        a.btn-ghost, button.btn-ghost {
            background: transparent; color: var(--ink-secondary);
            border: 1px solid var(--border-strong);
        }
        a.btn-ghost:hover, button.btn-ghost:hover {
            background: var(--paper-inset); color: var(--ink);
        }

        /* — badges — */
        .badge {
            display: inline-flex; align-items: center; gap: var(--sp-1);
            padding: 2px 8px; border-radius: 10px;
            font-size: 11px; font-weight: 600; letter-spacing: .01em;
        }
        .badge-ok   { background: var(--healthy-bg); color: var(--healthy); }
        .badge-warn { background: var(--warning-bg); color: var(--warning); }
        .badge-err  { background: var(--danger-bg);  color: var(--danger);  }

        /* — inline health dot — */
        .dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: var(--sp-1); flex-shrink: 0; }
        .dot-ok   { background: var(--healthy); }
        .dot-warn { background: var(--warning); }
        .dot-err  { background: var(--danger); }
        .dot-muted{ background: var(--ink-muted); }

        /* — pre/code — */
        pre {
            background: var(--ink); color: #e2e8f0;
            padding: var(--sp-4); border-radius: var(--radius-md);
            overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px; line-height: 1.6;
        }
        code {
            font-family: 'JetBrains Mono', monospace; font-size: 12px;
            background: var(--paper-inset); padding: 1px 5px; border-radius: var(--radius-sm);
        }

        /* — forms — */
        .muted { color: var(--ink-tertiary); font-size: 12.5px; }
        form.inline { display: flex; flex-wrap: wrap; gap: var(--sp-3); align-items: end; }
        label {
            font-weight: 500; color: var(--ink-secondary); font-size: 11px;
            text-transform: uppercase; letter-spacing: .04em;
            display: block; margin-bottom: var(--sp-1);
        }
        select, input {
            padding: var(--sp-2) var(--sp-3);
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-md);
            min-width: 160px; background: var(--paper-inset);
            font-family: inherit; font-size: 13px; color: var(--ink);
            transition: border-color .12s ease;
        }
        select:focus, input:focus { outline: none; border-color: var(--brand); }
        input[type=number] { min-width: 100px; }

        /* — alerts — */
        .warnbox {
            border: 1px solid rgba(212,148,10,.25); background: var(--warning-bg);
            color: #8a6914; padding: var(--sp-3) var(--sp-4);
            border-radius: var(--radius-md); margin-bottom: var(--sp-4); font-size: 12.5px;
        }
        .errbox {
            border: 1px solid rgba(196,72,62,.25); background: var(--danger-bg);
            color: var(--danger); padding: var(--sp-3) var(--sp-4);
            border-radius: var(--radius-md); margin-bottom: var(--sp-4); font-size: 12.5px;
        }

        /* — data table — */
        .table-wrap { overflow-x: auto; margin-top: var(--sp-4); border: 1px solid var(--border); border-radius: var(--radius-lg); }
        table { width: 100%; border-collapse: collapse; background: var(--paper-raised); }
        thead th {
            position: sticky; top: 0; background: var(--paper-inset);
            text-align: left; font-size: 11px; font-weight: 600;
            text-transform: uppercase; letter-spacing: .04em; color: var(--ink-tertiary);
            padding: var(--sp-2) var(--sp-3);
            border-bottom: 1px solid var(--border-strong); white-space: nowrap;
        }
        tbody td {
            padding: var(--sp-2) var(--sp-3);
            border-bottom: 1px solid var(--border-soft);
            font-size: 12.5px; font-variant-numeric: tabular-nums;
            vertical-align: middle; color: var(--ink);
        }
        tbody tr:hover { background: var(--brand-subtle); }
        .right { text-align: right; }
        .nowrap { white-space: nowrap; }

        /* — pager — */
        .pager { margin-top: var(--sp-4); display: flex; gap: var(--sp-3); align-items: center; flex-wrap: wrap; }

        /* — stat blocks — */
        .stat-row { display: flex; gap: var(--sp-4); flex-wrap: wrap; margin-bottom: var(--sp-4); }
        .stat-block {
            background: var(--paper-raised); border: 1px solid var(--border);
            border-radius: var(--radius-lg); padding: var(--sp-4) var(--sp-5);
            min-width: 180px; flex: 1;
        }
        .stat-block .stat-label {
            font-size: 11px; font-weight: 500; text-transform: uppercase;
            letter-spacing: .04em; color: var(--ink-tertiary); margin-bottom: var(--sp-1);
        }
        .stat-block .stat-value {
            font-size: 20px; font-weight: 700; color: var(--ink);
            letter-spacing: -.02em; font-variant-numeric: tabular-nums;
        }
        .stat-block .stat-meta { font-size: 11px; color: var(--ink-muted); margin-top: 2px; }
    </style>
</head>
<body>
<div class="shell">
    <aside class="sidebar">
        <div class="sidebar-brand">
            <h1>LinkedIn Ads</h1>
            <span>Action Center</span>
        </div>
        <div class="sidebar-section">Navigation</div>
        <nav>
            <a href="/" class="{{ 'active' if active_page == 'home' else '' }}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 6l6-4.5L14 6v7.5a1 1 0 01-1 1H3a1 1 0 01-1-1V6z"/><path d="M6 14.5V8h4v6.5"/></svg>
                Dashboard
            </a>
            <a href="/auth" class="{{ 'active' if active_page == 'auth' else '' }}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="7" width="12" height="7" rx="1"/><path d="M4.5 7V5a3.5 3.5 0 117 0v2"/></svg>
                Auth
            </a>
            <a href="/sync" class="{{ 'active' if active_page == 'sync' else '' }}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 8a7 7 0 0113.16-3.36"/><path d="M15 8a7 7 0 01-13.16 3.36"/><path d="M14.16 1v3.64H10.5"/><path d="M1.84 15v-3.64H5.5"/></svg>
                Sync Data
            </a>
        </nav>
        <div class="sidebar-section">Analysis</div>
        <nav>
            <a href="/report" class="{{ 'active' if active_page == 'report' else '' }}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 2v12h12"/><path d="M5 10V8"/><path d="M8 10V6"/><path d="M11 10V4"/></svg>
                Report
            </a>
            <a href="/status" class="{{ 'active' if active_page == 'status' else '' }}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 1.5"/></svg>
                Status
            </a>
        </nav>
    </aside>
    <div class="main">
        <header class="topbar">
            <h2>{{ page_title|safe }}</h2>
        </header>
        <div class="content">
            {{ content|safe }}
        </div>
    </div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _render(content_html: str, page_title: str = "", active_page: str = "") -> Response:
    response = make_response(render_template_string(
        LAYOUT, content=content_html, page_title=page_title, active_page=active_page
    ))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


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


def _latest_snapshot_path() -> Path | None:
    if not SNAPSHOT_DIR.exists():
        return None
    snaps = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return snaps[0] if snaps else None


# ---------------------------------------------------------------------------
# Data flattening (snapshot → table rows)
# ---------------------------------------------------------------------------

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
                opens = d.get("opens", 0) or 0
                sends = d.get("sends", 0) or 0
                social_actions = likes + comments + shares + follows
                engagements = clicks + social_actions
                cpm = (float(spend) / impressions * 1000.0) if impressions else 0.0
                engagement_rate = (engagements / impressions * 100.0) if impressions else 0.0
                conversions = d.get("conversions", 0) or 0
                cpc = d.get("cpc", 0.0) or 0.0
                ctr = d.get("ctr", 0.0) or 0.0
                cpa = (float(spend) / conversions) if conversions else 0.0
                cpl = (float(spend) / leads) if leads else 0.0
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
                    "Cost per Lead": cpl,
                    "Opens": opens,
                    "Sends": sends,
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
            opens = ms.get("opens", 0) or 0
            sends = ms.get("sends", 0) or 0
            conversions = ms.get("conversions", 0) or 0
            social_actions = likes + comments + shares + follows
            engagements = clicks + social_actions
            engagement_rate = (engagements / impressions * 100.0) if impressions else 0.0
            cpa = (float(spend) / conversions) if conversions else 0.0
            cpl = (float(spend) / leads) if leads else 0.0
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
                "Cost per Lead": cpl,
                "Opens": opens,
                "Sends": sends,
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
                leads = ms.get("leads", 0) or 0
                spend = ms.get("spend", 0.0) or 0.0
                cpl = (float(spend) / leads) if leads else 0.0
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
                    "Created At": _fmt_utc_ms(cr.get("created_at")),
                    "Last Modified At": _fmt_utc_ms(cr.get("last_modified_at")),
                    "Total Spent": spend,
                    "Impressions": ms.get("impressions", 0) or 0,
                    "Clicks": ms.get("clicks", 0) or 0,
                    "Click Through Rate": ms.get("ctr", 0.0) or 0.0,
                    "Average CPM": ms.get("cpm", 0.0) or 0.0,
                    "Average CPC": ms.get("cpc", 0.0) or 0.0,
                    "Reactions": ms.get("likes", 0) or 0,
                    "Comments": ms.get("comments", 0) or 0,
                    "Shares": ms.get("shares", 0) or 0,
                    "Follows": ms.get("follows", 0) or 0,
                    "Leads": leads,
                    "Cost per Lead": cpl,
                    "Opens": ms.get("opens", 0) or 0,
                    "Sends": ms.get("sends", 0) or 0,
                    "Conversions": ms.get("conversions", 0) or 0,
                })
    return out


def _flatten_campaign_settings(snapshot: dict) -> list[dict]:
    out: list[dict] = []
    for acct in snapshot.get("accounts", []):
        acct_name = acct.get("name", "")
        currency = acct.get("currency", "")
        for camp in acct.get("campaigns", []):
            settings = camp.get("settings", {}) or {}
            run_schedule = settings.get("run_schedule", {}) or {}
            camp_start_ms = run_schedule.get("start")
            camp_end_ms = run_schedule.get("end")
            out.append({
                "Account Name": acct_name,
                "Currency": currency,
                "Campaign Group ID": _extract_id(settings.get("campaign_group")),
                "Campaign ID": camp.get("id", ""),
                "Campaign Name": camp.get("name", ""),
                "Campaign Type": camp.get("type", ""),
                "Campaign Status": camp.get("status", ""),
                "Cost Type": settings.get("cost_type", ""),
                "Bid Strategy": settings.get("bid_strategy", ""),
                "Daily Budget": settings.get("daily_budget", ""),
                "Total Budget": settings.get("total_budget", ""),
                "Unit Cost": settings.get("unit_cost", ""),
                "Creative Selection": settings.get("creative_selection", ""),
                "Offsite Delivery Enabled": settings.get("offsite_delivery_enabled", ""),
                "Audience Expansion Enabled": settings.get("audience_expansion_enabled", ""),
                "Campaign Start Date": _fmt_utc_ms(camp_start_ms),
                "Campaign End Date": _fmt_utc_ms(camp_end_ms),
            })
    return out


# Well-known LinkedIn enum maps for display-time URN resolution
_SENIORITY_NAMES = {
    "1": "Unpaid", "2": "Training", "3": "Entry", "4": "Senior",
    "5": "Manager", "6": "Director", "7": "VP", "8": "CXO",
    "9": "Partner", "10": "Owner",
}
_COMPANY_SIZE_NAMES = {
    "A": "Self-employed (1)", "B": "2\u201310 employees", "C": "11\u201350 employees",
    "D": "51\u2013200 employees", "E": "201\u2013500 employees", "F": "501\u20131,000 employees",
    "G": "1,001\u20135,000 employees", "H": "5,001\u201310,000 employees", "I": "10,001+ employees",
}
_JOB_FUNCTION_NAMES = {
    "1": "Accounting", "2": "Administrative", "3": "Arts and Design",
    "4": "Business Development", "5": "Community & Social Services", "6": "Consulting",
    "7": "Education", "8": "Engineering", "9": "Entrepreneurship", "10": "Finance",
    "11": "Healthcare Services", "12": "Human Resources", "13": "Information Technology",
    "14": "Legal", "15": "Marketing", "16": "Media & Communications",
    "17": "Military & Protective Services", "18": "Operations", "19": "Product Management",
    "20": "Program & Project Management", "21": "Purchasing", "22": "Quality Assurance",
    "23": "Real Estate", "24": "Research", "25": "Sales", "26": "Customer Success & Support",
}


def _resolve_segment_name(segment: str) -> str:
    """Try to resolve a URN-style segment to a human-readable name using local maps."""
    if not segment or "urn:" not in segment:
        return segment
    parts = segment.split(":")
    if len(parts) < 4:
        return segment
    entity_type, entity_id = parts[2], parts[3]
    if entity_type == "seniority":
        return _SENIORITY_NAMES.get(entity_id, segment)
    if entity_type in ("companySizeRange", "companySize"):
        return _COMPANY_SIZE_NAMES.get(entity_id, segment)
    if entity_type == "function":
        return _JOB_FUNCTION_NAMES.get(entity_id, segment)
    return segment


# Module-level cache for API-resolved URN names (persists across requests)
_urn_api_cache: dict[str, str] = {}


def _resolve_urns_via_api(urns: list[str], auth_manager: AuthManager) -> dict[str, str]:
    """
    Batch-resolve URNs via LinkedIn /adTargetingEntities API.

    Results are cached in _urn_api_cache so the API is only called once per URN.
    """
    # Filter to URNs not already in cache
    to_resolve = [u for u in urns if u not in _urn_api_cache]
    if not to_resolve:
        return _urn_api_cache

    if not auth_manager.is_authenticated():
        return _urn_api_cache

    try:
        client = LinkedInClient(auth_manager)
        for i in range(0, len(to_resolve), 50):
            batch = to_resolve[i : i + 50]
            encoded = ",".join(u.replace(":", "%3A") for u in batch)
            try:
                data = client.get("/adTargetingEntities", f"q=urns&urns=List({encoded})")
                for elem in data.get("elements", []):
                    urn = elem.get("urn", "")
                    name = elem.get("name", "")
                    if urn and name:
                        _urn_api_cache[urn] = name
            except Exception:
                pass
    except Exception:
        pass

    # Mark URNs that couldn't be resolved so we don't retry them
    for u in to_resolve:
        if u not in _urn_api_cache:
            _urn_api_cache[u] = ""

    return _urn_api_cache


def _flatten_demographics(snapshot: dict, auth_manager: AuthManager | None = None) -> list[dict]:
    out: list[dict] = []

    # First pass: collect all raw segments that are still URNs after local resolution
    unresolved_urns: list[str] = []
    for acct in snapshot.get("accounts", []):
        demos = acct.get("audience_demographics", {}) or {}
        for pivot_type, segments in demos.items():
            for seg in segments or []:
                raw = seg.get("segment", "")
                if "urn:" in raw and _resolve_segment_name(raw) == raw:
                    unresolved_urns.append(raw)

    # Batch-resolve unresolved URNs via LinkedIn API
    api_names: dict[str, str] = {}
    if unresolved_urns and auth_manager is not None:
        api_names = _resolve_urns_via_api(unresolved_urns, auth_manager)

    # Second pass: build rows with fully resolved names
    for acct in snapshot.get("accounts", []):
        acct_name = acct.get("name", "")
        demos = acct.get("audience_demographics", {}) or {}
        for pivot_type, segments in demos.items():
            for seg in segments or []:
                raw = seg.get("segment", "")
                # Try: local enum map → API cache → raw URN
                display_name = _resolve_segment_name(raw)
                if display_name == raw and "urn:" in raw:
                    display_name = api_names.get(raw, "") or raw
                out.append({
                    "Account Name": acct_name,
                    "Pivot Type": pivot_type.replace("_", " ").title(),
                    "Segment": display_name,
                    "Impressions": seg.get("impressions", 0) or 0,
                    "Clicks": seg.get("clicks", 0) or 0,
                    "Click Through Rate": seg.get("ctr", 0.0) or 0.0,
                    "Share of Impressions": seg.get("share_of_impressions", 0.0) or 0.0,
                })
    return out


def _render_table(rows: list[dict], columns: list[str], page: int, page_size: int, mode: str = "", extra_params: str = "") -> str:
    total = len(rows)
    page_size = max(10, min(page_size, 500))
    max_page = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, max_page))
    start = (page - 1) * page_size
    end = min(total, start + page_size)

    def cell(col: str, v) -> str:
        cls = []
        if col in {"Impressions","Clicks","Reactions","Comments","Shares","Follows","Leads","Conversions","Clicks to Landing Page","Opens","Sends"}:
            cls.append("right")
            txt = _fmt_num(v, 0)
        elif col in {"Total Spent","Average CPM","Average CPC","Cost per Conversion","Cost per Lead","Daily Budget","Total Budget","Unit Cost"}:
            cls.append("right")
            txt = _fmt_num(v, 2)
        elif col in {"Click Through Rate","Engagement Rate","Share of Impressions"}:
            cls.append("right")
            txt = _fmt_pct(v, 2)
        else:
            txt = "" if v is None else str(v)
        if col in {"Start Date (in UTC)","Campaign Start Date","Campaign End Date","Created At","Last Modified At"}:
            cls.append("nowrap")
        return f'<td class="{" ".join(cls)}">{_h(txt)}</td>'

    thead = "<thead><tr>" + "".join(f"<th>{_h(c)}</th>" for c in columns) + "</tr></thead>"
    body_rows = []
    for r in rows[start:end]:
        body_rows.append("<tr>" + "".join(cell(c, r.get(c)) for c in columns) + "</tr>")
    tbody = "<tbody>" + "".join(body_rows) + "</tbody>"
    table = f'<div class="table-wrap"><table>{thead}{tbody}</table></div>'
    mode_param = f"&mode={_h(mode)}" if mode else ""
    pager = (
        f'<div class="pager">'
        f'<span class="muted">Rows {start+1:,}&ndash;{end:,} of {total:,} &middot; Page {page}/{max_page}</span>'
        f'<a class="btn-ghost btn" href="?page={max(1,page-1)}&page_size={page_size}{mode_param}{extra_params}">Prev</a>'
        f'<a class="btn-ghost btn" href="?page={min(max_page,page+1)}&page_size={page_size}{mode_param}{extra_params}">Next</a>'
        f'</div>'
    )
    return table + pager


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

def register_routes(app, auth_manager: AuthManager):
    """Attach all UI routes to the Flask app."""

    @app.route("/")
    def home():
        html = """
        <div class="action-grid">
            <div class="action-card">
                <div class="step-num">1</div>
                <h3>Authenticate</h3>
                <p>Connect your LinkedIn account via OAuth. Required before syncing data.</p>
                <a class="btn" href="/auth">Connect Account</a>
            </div>
            <div class="action-card">
                <div class="step-num">2</div>
                <h3>Sync Data</h3>
                <p>Pull ad accounts, campaigns, creatives and 90 days of performance metrics.</p>
                <a class="btn" href="/sync">Sync Now</a>
            </div>
            <div class="action-card">
                <div class="step-num">3</div>
                <h3>Explore Reports</h3>
                <p>Campaign daily metrics, summary rollups, and creative performance breakdowns.</p>
                <a class="btn-ghost btn" href="/report">Open Report</a>
            </div>
            <div class="action-card">
                <div class="step-num">4</div>
                <h3>System Status</h3>
                <p>Token health, database row counts, and active campaign audit results.</p>
                <a class="btn-ghost btn" href="/status">View Status</a>
            </div>
        </div>
        """
        return _render(html, page_title="Dashboard", active_page="home")

    @app.route("/auth")
    def auth():
        if auth_manager.is_authenticated():
            status = auth_manager.token_status()
            badge = "badge-ok" if not status["access_token_expired"] else "badge-err"
            html = f"""
            <div class="card">
                <h3><span class="dot dot-ok"></span> Connected <span class="badge {badge}">Active</span></h3>
                <div class="stat-row" style="margin-top:16px">
                    <div class="stat-block">
                        <div class="stat-label">Access Token</div>
                        <div class="stat-value">{status['access_token_days_remaining']}d</div>
                        <div class="stat-meta">remaining</div>
                    </div>
                    <div class="stat-block">
                        <div class="stat-label">Refresh Token</div>
                        <div class="stat-value">{status.get('refresh_token_days_remaining', 'N/A')}d</div>
                        <div class="stat-meta">remaining</div>
                    </div>
                </div>
                <p class="muted">Last saved: {status.get('saved_at', 'unknown')}</p>
            </div>
            """
            return _render(html, page_title='Authentication <span class="badge badge-ok">Connected</span>', active_page="auth")

        auth_url = auth_manager.get_authorization_url()
        return redirect(auth_url)

    @app.route("/callback")
    def callback():
        state = request.args.get("state")
        if state != OAUTH_STATE:
            return _render('<div class="errbox"><strong>Error:</strong> Invalid state parameter.</div>',
                           page_title="Auth Error", active_page="auth"), 400

        error = request.args.get("error")
        if error:
            desc = request.args.get("error_description", "")
            return _render(f'<div class="errbox"><strong>OAuth Error:</strong> {_h(error)}: {_h(desc)}</div>',
                           page_title="Auth Error", active_page="auth"), 400

        code = request.args.get("code")
        if not code:
            return _render('<div class="errbox"><strong>Error:</strong> No authorization code received.</div>',
                           page_title="Auth Error", active_page="auth"), 400

        try:
            auth_manager.exchange_code_for_token(code)
        except Exception as exc:
            return _render(f'<div class="errbox"><strong>Token Exchange Failed</strong></div><pre>{_h(str(exc))}</pre>',
                           page_title="Auth Error", active_page="auth"), 500

        status = auth_manager.token_status()
        html = f"""
        <div class="card">
            <h3><span class="dot dot-ok"></span> Authentication Successful <span class="badge badge-ok">Connected</span></h3>
            <div class="stat-row" style="margin-top:16px">
                <div class="stat-block">
                    <div class="stat-label">Access Token</div>
                    <div class="stat-value">{status['access_token_days_remaining']}d</div>
                    <div class="stat-meta">remaining</div>
                </div>
                <div class="stat-block">
                    <div class="stat-label">Refresh Token</div>
                    <div class="stat-value">{status.get('refresh_token_days_remaining', 'N/A')}d</div>
                    <div class="stat-meta">remaining</div>
                </div>
            </div>
            <a class="btn" href="/" style="margin-top:12px">Go to Dashboard</a>
        </div>
        """
        return _render(html, page_title='Authentication <span class="badge badge-ok">Connected</span>', active_page="auth")

    @app.route("/sync")
    def sync():
        if not auth_manager.is_authenticated():
            return _render('<div class="warnbox"><strong>Not Authenticated.</strong> Please <a href="/auth">connect your account</a> first.</div>',
                           page_title="Sync Data", active_page="sync"), 401

        logs: list[str] = []
        try:
            client = LinkedInClient(auth_manager)
            today = datetime.now(tz=timezone.utc).date()
            date_start = today - timedelta(days=90)
            logs.append(f"Date range: {date_start} → {today}  ({(today - date_start).days} days)")

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
                # Resolve demographic URNs to human-readable names
                urn_names = resolve_demographic_urns(client, demo)
                demographics_by_account[acct_id] = {"pivots": demo, "urn_names": urn_names}
                logs.append(f"  Account {acct_id}: demographics pivots {len(demo)}, resolved {len(urn_names)} URNs")

            camp_metrics = fetch_campaign_metrics(client, [c["id"] for c in all_campaigns], date_start, today)
            logs.append(f"Campaign metric rows: {len(camp_metrics)}")

            creative_metrics = fetch_creative_metrics(client, [c["id"] for c in all_campaigns], date_start, today)
            logs.append(f"Creative metric rows: {len(creative_metrics)}")

            snapshot = assemble_snapshot(accounts, all_campaigns, all_creatives,
                                         camp_metrics, creative_metrics, demographics_by_account,
                                         date_start, today)
            save_snapshot_json(snapshot)
            persist_snapshot(snapshot)
            logs.append("Snapshot saved to JSON and SQLite.")
        except Exception as exc:
            logs.append(f"\nERROR: {exc}")

        pre = "\n".join(logs)
        html = f'<div class="card"><pre>{_h(pre)}</pre></div><a class="btn-ghost btn" href="/">Back to Dashboard</a>'
        return _render(html, page_title="Sync Results", active_page="sync")

    @app.route("/status")
    def status():
        ts = auth_manager.token_status()
        is_auth = ts.get("authenticated", False)

        if is_auth:
            token_dot = "dot-ok"
            token_label = "Connected"
            access_val = f"{ts['access_token_days_remaining']}d"
            refresh_val = f"{ts.get('refresh_token_days_remaining', 'N/A')}d"
            saved_at = ts.get("saved_at", "N/A")
        else:
            token_dot = "dot-err"
            token_label = "Not Connected"
            access_val = "\u2014"
            refresh_val = "\u2014"
            saved_at = "\u2014"

        html = f"""
        <div class="card">
            <h3><span class="dot {token_dot}"></span> Token: {_h(token_label)}</h3>
            <div class="stat-row" style="margin-top:12px">
                <div class="stat-block">
                    <div class="stat-label">Access Token</div>
                    <div class="stat-value">{_h(access_val)}</div>
                    <div class="stat-meta">remaining</div>
                </div>
                <div class="stat-block">
                    <div class="stat-label">Refresh Token</div>
                    <div class="stat-value">{_h(refresh_val)}</div>
                    <div class="stat-meta">remaining</div>
                </div>
                <div class="stat-block">
                    <div class="stat-label">Last Saved</div>
                    <div class="stat-value" style="font-size:14px">{_h(saved_at)}</div>
                </div>
            </div>
        </div>
        """

        try:
            counts = table_counts()
            html += '<div class="card"><h3>Database</h3><div class="stat-row" style="margin-top:12px">'
            for tbl, cnt in counts.items():
                html += f'<div class="stat-block"><div class="stat-label">{_h(tbl)}</div><div class="stat-value">{cnt:,}</div><div class="stat-meta">rows</div></div>'
            html += '</div></div>'
        except Exception as exc:
            html += f'<div class="errbox">Database error: {_h(str(exc))}</div>'

        try:
            audit = active_campaign_audit()
            if audit:
                html += f'<div class="card"><h3><span class="dot dot-ok"></span> Active Campaigns</h3><p style="margin-top:8px">{len(audit)} campaigns currently active</p></div>'
        except Exception:
            pass

        badge = "badge-ok" if is_auth else "badge-err"
        label = "Healthy" if is_auth else "Action Required"
        return _render(html, page_title=f'System Status <span class="badge {badge}">{_h(label)}</span>', active_page="status")

    @app.route("/report")
    def report():
        snap_path = _latest_snapshot_path()
        if not snap_path:
            return _render('<div class="card"><h3>No snapshot found</h3><p>Run a <a href="/sync">Sync</a> first to pull data.</p></div>',
                           page_title="Report", active_page="report")

        mode = request.args.get("mode", "campaign_daily")
        page = int(request.args.get("page", "1") or "1")
        page_size = int(request.args.get("page_size", "50") or "50")

        snapshot = json.loads(Path(snap_path).read_text(encoding="utf-8"))

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
                '<div class="warnbox"><strong>Warning:</strong> This snapshot has duplicate campaign IDs '
                'across accounts. Run <a href="/sync">Sync</a> again to generate a corrected snapshot.</div>'
            )

        options = {
            "campaign_daily": "Campaign Daily (time series)",
            "campaign_summary": "Campaign Summary (90d total)",
            "creative_summary": "Creative Summary (90d total)",
            "campaign_settings": "Campaign Settings",
            "demographics": "Audience Demographics",
        }
        mode_label = options.get(mode, options["campaign_daily"])

        if mode == "campaign_summary":
            rows = _flatten_campaign_summary(snapshot)
            columns = [
                "Account Name","Currency","Campaign Group ID","Campaign ID","Campaign Name","Campaign Type","Campaign Status",
                "Cost Type","Daily Budget","Campaign Start Date",
                "Total Spent","Impressions","Clicks","Click Through Rate","Average CPM","Average CPC",
                "Reactions","Comments","Shares","Follows","Leads","Cost per Lead","Opens","Sends",
                "Clicks to Landing Page","Conversions","Cost per Conversion",
                "Total Social Actions","Total Engagements","Engagement Rate",
            ]
        elif mode == "creative_summary":
            rows = _flatten_creative_summary(snapshot)
            columns = [
                "Account Name","Currency","Campaign ID","Campaign Name",
                "Creative ID","Creative Intended Status","Creative Is Serving","Serving Hold Reasons","Content Reference",
                "Created At","Last Modified At",
                "Total Spent","Impressions","Clicks","Click Through Rate","Average CPM","Average CPC",
                "Reactions","Comments","Shares","Follows","Leads","Cost per Lead","Opens","Sends","Conversions",
            ]
        elif mode == "campaign_settings":
            rows = _flatten_campaign_settings(snapshot)
            columns = [
                "Account Name","Currency","Campaign Group ID","Campaign ID","Campaign Name","Campaign Type","Campaign Status",
                "Cost Type","Bid Strategy","Daily Budget","Total Budget","Unit Cost",
                "Creative Selection","Offsite Delivery Enabled","Audience Expansion Enabled",
                "Campaign Start Date","Campaign End Date",
            ]
        elif mode == "demographics":
            rows = _flatten_demographics(snapshot, auth_manager=auth_manager)
            pivot_filter = request.args.get("pivot", "")
            if pivot_filter:
                rows = [r for r in rows if r.get("Pivot Type") == pivot_filter]
            columns = [
                "Account Name","Pivot Type","Segment",
                "Impressions","Clicks","Click Through Rate","Share of Impressions",
            ]
        else:
            rows = _flatten_campaign_daily(snapshot)
            columns = [
                "Start Date (in UTC)","Account Name","Currency","Campaign Group ID","Campaign ID","Campaign Name","Campaign Type","Campaign Status",
                "Cost Type","Daily Budget","Campaign Start Date",
                "Total Spent","Impressions","Clicks","Click Through Rate","Average CPM","Average CPC",
                "Reactions","Comments","Shares","Follows","Leads","Cost per Lead","Opens","Sends",
                "Clicks to Landing Page","Conversions","Cost per Conversion",
                "Total Social Actions","Total Engagements","Engagement Rate",
            ]

        rows.sort(key=lambda r: (r.get("Account Name",""), r.get("Campaign Name",""), r.get("Start Date (in UTC)","")))
        total_rows = len(rows)

        # Build pivot filter dropdown for demographics mode
        pivot_html = ""
        if mode == "demographics":
            pivot_filter = request.args.get("pivot", "")
            pivot_options = {
                "": "All Pivots",
                "Job Title": "Job Title",
                "Job Function": "Job Function",
                "Industry": "Industry",
                "Seniority": "Seniority",
                "Company Size": "Company Size",
                "Country V2": "Country",
            }
            pivot_html = (
                '  <div><label for="pivot">Pivot Type</label><select name="pivot" id="pivot">'
                + "".join([f'<option value="{_h(k)}" {"selected" if k==pivot_filter else ""}>{_h(v)}</option>' for k,v in pivot_options.items()])
                + '</select></div>'
            )

        form = (
            f'<div class="card">'
            f'<p class="muted">Snapshot: <code>{_h(str(snap_path.name))}</code> &middot; {total_rows:,} rows</p>'
            f'{warn_html}'
            f'<form class="inline" method="get" style="margin-top:12px">'
            f'  <div><label for="mode">View</label><select name="mode" id="mode">'
            + "".join([f'<option value="{k}" {"selected" if k==mode else ""}>{_h(v)}</option>' for k,v in options.items()])
            + f'</select></div>'
            + pivot_html
            + f'  <div><label for="page_size">Rows</label><input type="number" min="10" max="500" name="page_size" id="page_size" value="{page_size}"></div>'
            f'  <div><button class="btn" type="submit">Apply</button></div>'
            f'</form>'
            f'</div>'
        )

        extra_params = ""
        if mode == "demographics":
            pf = request.args.get("pivot", "")
            if pf:
                extra_params = f"&pivot={_h(pf)}"
        table_html = _render_table(rows, columns, page=page, page_size=page_size, mode=mode, extra_params=extra_params)
        return _render(form + table_html, page_title=f"Report &middot; {_h(mode_label)}", active_page="report")
