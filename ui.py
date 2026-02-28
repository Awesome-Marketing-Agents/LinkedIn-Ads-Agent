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
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
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
            <a href="/report/visual" class="{{ 'active' if active_page == 'visual' else '' }}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 2v12h12"/><path d="M5 11l3-4 2 2 3-4"/></svg>
                Visual Dashboard
            </a>
            <a href="/report" class="{{ 'active' if active_page == 'report' else '' }}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 2v12h12"/><path d="M5 10V8"/><path d="M8 10V6"/><path d="M11 10V4"/></svg>
                Report Tables
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
# Visual dashboard data preparation
# ---------------------------------------------------------------------------

def _prepare_kpi_data(snapshot: dict) -> dict:
    """Aggregate top-level KPIs across all campaigns."""
    totals = dict(spend=0.0, impressions=0, clicks=0, leads=0, conversions=0, landing_page_clicks=0,
                  likes=0, comments=0, shares=0, follows=0)
    campaign_count = 0
    for acct in snapshot.get("accounts", []):
        for camp in acct.get("campaigns", []):
            campaign_count += 1
            ms = camp.get("metrics_summary") or {}
            for k in totals:
                totals[k] += ms.get(k, 0) or 0
    ctr = (totals["clicks"] / totals["impressions"] * 100) if totals["impressions"] else 0
    cpc = (totals["spend"] / totals["clicks"]) if totals["clicks"] else 0
    cpl = (totals["spend"] / totals["leads"]) if totals["leads"] else 0
    return {**totals, "ctr": ctr, "cpc": cpc, "cpl": cpl, "campaign_count": campaign_count}


def _prepare_timeseries_data(snapshot: dict) -> dict:
    """Aggregate daily metrics across all campaigns by date."""
    by_date: dict[str, dict] = {}
    for acct in snapshot.get("accounts", []):
        for camp in acct.get("campaigns", []):
            for d in camp.get("daily_metrics") or []:
                date = d.get("date", "")
                if not date:
                    continue
                if date not in by_date:
                    by_date[date] = dict(spend=0.0, impressions=0, clicks=0, conversions=0, leads=0)
                by_date[date]["spend"] += (d.get("spend", 0) or 0)
                by_date[date]["impressions"] += (d.get("impressions", 0) or 0)
                by_date[date]["clicks"] += (d.get("clicks", 0) or 0)
                by_date[date]["conversions"] += (d.get("conversions", 0) or 0)
                by_date[date]["leads"] += (d.get("leads", 0) or 0)
    dates = sorted(by_date.keys())
    return {
        "labels": dates,
        "spend": [by_date[d]["spend"] for d in dates],
        "impressions": [by_date[d]["impressions"] for d in dates],
        "clicks": [by_date[d]["clicks"] for d in dates],
        "conversions": [by_date[d]["conversions"] for d in dates],
        "leads": [by_date[d]["leads"] for d in dates],
    }


def _prepare_campaign_comparison(snapshot: dict) -> dict:
    """Per-campaign metrics for bar chart comparisons."""
    campaigns = []
    for acct in snapshot.get("accounts", []):
        for camp in acct.get("campaigns", []):
            ms = camp.get("metrics_summary") or {}
            impressions = ms.get("impressions", 0) or 0
            clicks = ms.get("clicks", 0) or 0
            spend = ms.get("spend", 0) or 0
            name = camp.get("name", f"Campaign {camp.get('id', '?')}")
            if len(name) > 35:
                name = name[:32] + "..."
            campaigns.append({
                "name": name,
                "impressions": impressions,
                "clicks": clicks,
                "spend": round(spend, 2),
                "ctr": round(clicks / impressions * 100, 2) if impressions else 0,
                "cpc": round(spend / clicks, 2) if clicks else 0,
                "conversions": ms.get("conversions", 0) or 0,
                "leads": ms.get("leads", 0) or 0,
            })
    campaigns.sort(key=lambda c: c["spend"], reverse=True)
    return {"campaigns": campaigns[:20]}


def _prepare_demographics(snapshot: dict) -> dict:
    """Collect demographic data across all accounts."""
    all_demos: dict[str, list] = {}
    dimension_labels = {
        "jobtitle": "Job Title", "jobfunction": "Job Function",
        "industry": "Industry", "seniority": "Seniority",
        "company_size": "Company Size", "country_v2": "Country",
    }
    for acct in snapshot.get("accounts", []):
        demos = acct.get("audience_demographics") or {}
        for key, segments in demos.items():
            if key not in all_demos:
                all_demos[key] = []
            all_demos[key].extend(segments or [])
    # Merge duplicate segments and take top 10
    result = {}
    for key, segments in all_demos.items():
        merged: dict[str, dict] = {}
        for s in segments:
            seg_name = s.get("segment", "Unknown")
            if seg_name in merged:
                merged[seg_name]["impressions"] += s.get("impressions", 0) or 0
                merged[seg_name]["clicks"] += s.get("clicks", 0) or 0
            else:
                merged[seg_name] = {
                    "segment": seg_name,
                    "impressions": s.get("impressions", 0) or 0,
                    "clicks": s.get("clicks", 0) or 0,
                    "share": s.get("share_of_impressions", 0) or 0,
                }
        top = sorted(merged.values(), key=lambda x: x["impressions"], reverse=True)[:10]
        result[key] = {
            "label": dimension_labels.get(key, key),
            "segments": [s["segment"] for s in top],
            "impressions": [s["impressions"] for s in top],
            "share": [round(s["share"], 1) for s in top],
        }
    return result


def _prepare_budget_utilization(snapshot: dict) -> list[dict]:
    """Budget utilization per campaign."""
    items = []
    for acct in snapshot.get("accounts", []):
        for camp in acct.get("campaigns", []):
            settings = camp.get("settings") or {}
            try:
                daily_budget = float(settings.get("daily_budget") or 0)
            except (TypeError, ValueError):
                continue
            if not daily_budget:
                continue
            ms = camp.get("metrics_summary") or {}
            spend = float(ms.get("spend", 0) or 0)
            days_active = len(camp.get("daily_metrics") or [])
            if days_active == 0:
                continue
            total_budget = daily_budget * days_active
            utilization = (spend / total_budget * 100) if total_budget else 0
            name = camp.get("name", f"Campaign {camp.get('id', '?')}")
            if len(name) > 35:
                name = name[:32] + "..."
            items.append({
                "name": name,
                "daily_budget": round(daily_budget, 2),
                "total_budget": round(total_budget, 2),
                "spend": round(spend, 2),
                "utilization": round(min(utilization, 100), 1),
                "days_active": days_active,
            })
    items.sort(key=lambda x: x["utilization"], reverse=True)
    return items[:15]


def _prepare_spend_distribution(snapshot: dict) -> dict:
    """Spend distribution across campaigns for donut chart."""
    items = []
    for acct in snapshot.get("accounts", []):
        for camp in acct.get("campaigns", []):
            ms = camp.get("metrics_summary") or {}
            spend = ms.get("spend", 0) or 0
            if spend <= 0:
                continue
            name = camp.get("name", f"Campaign {camp.get('id', '?')}")
            if len(name) > 30:
                name = name[:27] + "..."
            items.append({"name": name, "spend": round(spend, 2)})
    items.sort(key=lambda x: x["spend"], reverse=True)
    # Group small campaigns into "Other" if more than 8
    if len(items) > 8:
        top = items[:7]
        other_spend = sum(i["spend"] for i in items[7:])
        top.append({"name": "Other", "spend": round(other_spend, 2)})
        items = top
    return {"labels": [i["name"] for i in items], "values": [i["spend"] for i in items]}


def _prepare_funnel_data(snapshot: dict) -> dict:
    """Conversion funnel across all campaigns."""
    totals = dict(impressions=0, clicks=0, landing_page_clicks=0, conversions=0, leads=0)
    for acct in snapshot.get("accounts", []):
        for camp in acct.get("campaigns", []):
            ms = camp.get("metrics_summary") or {}
            for k in totals:
                totals[k] += ms.get(k, 0) or 0
    return totals


def _prepare_engagement_radar(snapshot: dict) -> dict:
    """Radar chart data for top campaigns by engagement quality."""
    campaigns = []
    for acct in snapshot.get("accounts", []):
        for camp in acct.get("campaigns", []):
            ms = camp.get("metrics_summary") or {}
            impressions = ms.get("impressions", 0) or 0
            clicks = ms.get("clicks", 0) or 0
            spend = ms.get("spend", 0) or 0
            if impressions == 0:
                continue
            likes = ms.get("likes", 0) or 0
            comments = ms.get("comments", 0) or 0
            shares = ms.get("shares", 0) or 0
            follows = ms.get("follows", 0) or 0
            conversions = ms.get("conversions", 0) or 0
            social = likes + comments + shares + follows
            name = camp.get("name", f"Campaign {camp.get('id', '?')}")
            if len(name) > 25:
                name = name[:22] + "..."
            campaigns.append({
                "name": name,
                "ctr": clicks / impressions * 100,
                "engagement_rate": (clicks + social) / impressions * 100,
                "social_rate": social / impressions * 100,
                "conversion_rate": conversions / clicks * 100 if clicks else 0,
                "cpc_efficiency": min(100, 100 / (spend / clicks)) if clicks and spend else 0,
            })
    campaigns.sort(key=lambda c: c["engagement_rate"], reverse=True)
    return {"campaigns": campaigns[:5]}


def _prepare_creative_comparison(snapshot: dict) -> dict:
    """Creative performance comparison data."""
    creatives = []
    for acct in snapshot.get("accounts", []):
        for camp in acct.get("campaigns", []):
            camp_name = camp.get("name", f"Campaign {camp.get('id', '?')}")
            for cr in camp.get("creatives") or []:
                ms = cr.get("metrics_summary") or {}
                impressions = ms.get("impressions", 0) or 0
                if impressions == 0:
                    continue
                clicks = ms.get("clicks", 0) or 0
                spend = ms.get("spend", 0) or 0
                cr_id = _extract_id(cr.get("id"))
                label = f"{camp_name[:20]}/ Cr {cr_id}"
                creatives.append({
                    "label": label,
                    "impressions": impressions,
                    "clicks": clicks,
                    "spend": round(spend, 2),
                    "ctr": round(clicks / impressions * 100, 2) if impressions else 0,
                    "conversions": ms.get("conversions", 0) or 0,
                    "is_serving": cr.get("is_serving", False),
                })
    creatives.sort(key=lambda c: c["impressions"], reverse=True)
    return {"creatives": creatives[:15]}


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
                <p>Visual dashboard with charts, trends, and detailed data tables.</p>
                <a class="btn-ghost btn" href="/report/visual">Visual Dashboard</a>
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

    @app.route("/report/visual")
    def report_visual():
        snap_path = _latest_snapshot_path()
        if not snap_path:
            return _render(
                '<div class="card"><h3>No snapshot found</h3>'
                '<p>Run a <a href="/sync">Sync</a> first to pull data.</p></div>',
                page_title="Visual Dashboard", active_page="visual")

        snapshot = json.loads(Path(snap_path).read_text(encoding="utf-8"))

        kpi = _prepare_kpi_data(snapshot)
        ts = _prepare_timeseries_data(snapshot)
        comparison = _prepare_campaign_comparison(snapshot)
        demographics = _prepare_demographics(snapshot)
        budget = _prepare_budget_utilization(snapshot)
        spend_dist = _prepare_spend_distribution(snapshot)
        funnel = _prepare_funnel_data(snapshot)
        radar = _prepare_engagement_radar(snapshot)
        creatives = _prepare_creative_comparison(snapshot)

        # Chart color palette
        colors = [
            "#2b6cb0", "#2d8a6e", "#d4940a", "#c4483e", "#6b46c1",
            "#d53f8c", "#2c7a7b", "#c05621", "#5a67d8", "#38a169",
        ]

        html = f"""
        <style>
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: var(--sp-4);
                margin-bottom: var(--sp-6);
            }}
            .kpi-card {{
                background: var(--paper-raised);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: var(--sp-5);
                text-align: center;
            }}
            .kpi-card .kpi-value {{
                font-size: 26px;
                font-weight: 700;
                color: var(--ink);
                letter-spacing: -.02em;
                font-variant-numeric: tabular-nums;
            }}
            .kpi-card .kpi-label {{
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: .04em;
                color: var(--ink-tertiary);
                margin-top: var(--sp-1);
            }}
            .chart-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: var(--sp-4);
                margin-bottom: var(--sp-4);
            }}
            .chart-grid .full-width {{
                grid-column: 1 / -1;
            }}
            .chart-card {{
                background: var(--paper-raised);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: var(--sp-6);
            }}
            .chart-card h3 {{
                margin-bottom: var(--sp-4);
                font-size: 13px;
                font-weight: 600;
            }}
            .chart-container {{
                position: relative;
                width: 100%;
            }}
            .chart-container canvas {{
                width: 100% !important;
            }}
            .funnel-bar {{
                display: flex;
                align-items: center;
                margin-bottom: var(--sp-2);
            }}
            .funnel-bar .funnel-label {{
                width: 140px;
                font-size: 12px;
                font-weight: 500;
                color: var(--ink-secondary);
                text-align: right;
                padding-right: var(--sp-3);
                flex-shrink: 0;
            }}
            .funnel-bar .funnel-track {{
                flex: 1;
                height: 32px;
                background: var(--paper-inset);
                border-radius: var(--radius-sm);
                overflow: hidden;
                position: relative;
            }}
            .funnel-bar .funnel-fill {{
                height: 100%;
                border-radius: var(--radius-sm);
                display: flex;
                align-items: center;
                padding-left: var(--sp-3);
                font-size: 12px;
                font-weight: 600;
                color: #fff;
                min-width: 40px;
                transition: width 0.6s ease;
            }}
            .funnel-bar .funnel-value {{
                margin-left: var(--sp-2);
                font-size: 12px;
                font-weight: 600;
                color: var(--ink);
                white-space: nowrap;
            }}
            .budget-item {{
                display: flex;
                align-items: center;
                margin-bottom: var(--sp-3);
                gap: var(--sp-3);
            }}
            .budget-item .budget-name {{
                width: 180px;
                font-size: 12px;
                font-weight: 500;
                color: var(--ink-secondary);
                text-align: right;
                flex-shrink: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .budget-item .budget-track {{
                flex: 1;
                height: 20px;
                background: var(--paper-inset);
                border-radius: 10px;
                overflow: hidden;
            }}
            .budget-item .budget-fill {{
                height: 100%;
                border-radius: 10px;
                transition: width 0.6s ease;
            }}
            .budget-item .budget-pct {{
                width: 50px;
                font-size: 12px;
                font-weight: 600;
                color: var(--ink);
                text-align: right;
            }}
            .section-title {{
                font-size: 16px;
                font-weight: 700;
                color: var(--ink);
                margin: var(--sp-8) 0 var(--sp-4);
                padding-bottom: var(--sp-2);
                border-bottom: 1px solid var(--border);
            }}
            .section-title:first-child {{
                margin-top: 0;
            }}
            .metric-selector {{
                display: flex;
                gap: var(--sp-2);
                margin-bottom: var(--sp-3);
                flex-wrap: wrap;
            }}
            .metric-btn {{
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                cursor: pointer;
                border: 1px solid var(--border-strong);
                background: var(--paper-inset);
                color: var(--ink-secondary);
                transition: all .15s ease;
            }}
            .metric-btn.active {{
                background: var(--brand);
                color: #fff;
                border-color: var(--brand);
            }}
            .metric-btn:hover {{
                border-color: var(--brand);
            }}
            @media (max-width: 900px) {{
                .chart-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>

        <p class="muted" style="margin-bottom: var(--sp-4)">
            Snapshot: <code>{_h(str(snap_path.name))}</code> &middot;
            {kpi['campaign_count']} campaigns &middot;
            <a href="/report">View data tables</a>
        </p>

        <!-- ============ P0: KPI SCORECARDS ============ -->
        <div class="section-title" style="margin-top:0">Performance Overview</div>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value">${kpi['spend']:,.2f}</div>
                <div class="kpi-label">Total Spend</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{kpi['impressions']:,}</div>
                <div class="kpi-label">Impressions</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{kpi['clicks']:,}</div>
                <div class="kpi-label">Clicks</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{kpi['ctr']:.2f}%</div>
                <div class="kpi-label">CTR</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">${kpi['cpc']:.2f}</div>
                <div class="kpi-label">Avg CPC</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{kpi['leads']:,}</div>
                <div class="kpi-label">Leads</div>
            </div>
        </div>

        <div class="chart-grid">

        <!-- ============ P0: PERFORMANCE TRENDS ============ -->
        <div class="chart-card full-width">
            <h3>Performance Trends (Daily)</h3>
            <div class="metric-selector" id="trend-metrics">
                <button class="metric-btn active" data-dataset="0">Spend ($)</button>
                <button class="metric-btn active" data-dataset="1">Impressions</button>
                <button class="metric-btn" data-dataset="2">Clicks</button>
                <button class="metric-btn" data-dataset="3">Conversions</button>
                <button class="metric-btn" data-dataset="4">Leads</button>
            </div>
            <div class="chart-container"><canvas id="trendChart"></canvas></div>
        </div>

        <!-- ============ P0: CAMPAIGN COMPARISON ============ -->
        <div class="chart-card full-width">
            <h3>Campaign Comparison</h3>
            <div class="metric-selector" id="compare-metrics">
                <button class="metric-btn active" data-metric="spend">Spend ($)</button>
                <button class="metric-btn" data-metric="impressions">Impressions</button>
                <button class="metric-btn" data-metric="clicks">Clicks</button>
                <button class="metric-btn" data-metric="ctr">CTR (%)</button>
                <button class="metric-btn" data-metric="cpc">CPC ($)</button>
                <button class="metric-btn" data-metric="conversions">Conversions</button>
            </div>
            <div class="chart-container"><canvas id="compareChart"></canvas></div>
        </div>

        <!-- ============ P1: SPEND DISTRIBUTION ============ -->
        <div class="chart-card">
            <h3>Spend Distribution</h3>
            <div class="chart-container" style="max-width:380px;margin:0 auto"><canvas id="spendDonut"></canvas></div>
        </div>

        <!-- ============ P2: CONVERSION FUNNEL ============ -->
        <div class="chart-card">
            <h3>Conversion Funnel</h3>
            <div id="funnelContainer" style="padding: var(--sp-2) 0"></div>
        </div>

        <!-- ============ P1: BUDGET UTILIZATION ============ -->
        <div class="chart-card full-width">
            <h3>Budget Utilization</h3>
            <div id="budgetContainer"></div>
        </div>

        <!-- ============ P2: ENGAGEMENT RADAR ============ -->
        <div class="chart-card">
            <h3>Engagement Quality (Top 5 Campaigns)</h3>
            <div class="chart-container"><canvas id="radarChart"></canvas></div>
        </div>

        <!-- ============ P2: CREATIVE PERFORMANCE ============ -->
        <div class="chart-card">
            <h3>Creative Performance</h3>
            <div class="chart-container"><canvas id="creativeChart"></canvas></div>
        </div>

        </div><!-- end chart-grid -->

        <!-- ============ P1: DEMOGRAPHICS ============ -->
        <div class="section-title">Audience Demographics</div>
        <div class="chart-grid" id="demoCharts"></div>

        <script>
        (function() {{
            const COLORS = {json.dumps(colors)};

            // ---- Trend Chart ----
            const tsData = {json.dumps(ts)};
            const trendCtx = document.getElementById('trendChart').getContext('2d');
            const trendChart = new Chart(trendCtx, {{
                type: 'line',
                data: {{
                    labels: tsData.labels,
                    datasets: [
                        {{ label: 'Spend ($)', data: tsData.spend, borderColor: COLORS[0], backgroundColor: COLORS[0]+'20', tension: 0.3, yAxisID: 'y', hidden: false, fill: true }},
                        {{ label: 'Impressions', data: tsData.impressions, borderColor: COLORS[1], backgroundColor: COLORS[1]+'20', tension: 0.3, yAxisID: 'y1', hidden: false, fill: false }},
                        {{ label: 'Clicks', data: tsData.clicks, borderColor: COLORS[2], backgroundColor: COLORS[2]+'20', tension: 0.3, yAxisID: 'y1', hidden: true, fill: false }},
                        {{ label: 'Conversions', data: tsData.conversions, borderColor: COLORS[3], backgroundColor: COLORS[3]+'20', tension: 0.3, yAxisID: 'y1', hidden: true, fill: false }},
                        {{ label: 'Leads', data: tsData.leads, borderColor: COLORS[4], backgroundColor: COLORS[4]+'20', tension: 0.3, yAxisID: 'y1', hidden: true, fill: false }},
                    ]
                }},
                options: {{
                    responsive: true,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        x: {{ ticks: {{ maxTicksLimit: 15, font: {{ size: 10 }} }} }},
                        y: {{ position: 'left', title: {{ display: true, text: 'Spend ($)' }}, grid: {{ drawOnChartArea: true }} }},
                        y1: {{ position: 'right', title: {{ display: true, text: 'Count' }}, grid: {{ drawOnChartArea: false }} }}
                    }}
                }}
            }});

            // Toggle trend datasets
            document.getElementById('trend-metrics').addEventListener('click', function(e) {{
                const btn = e.target.closest('.metric-btn');
                if (!btn) return;
                const idx = parseInt(btn.dataset.dataset);
                btn.classList.toggle('active');
                const meta = trendChart.getDatasetMeta(idx);
                meta.hidden = !btn.classList.contains('active');
                trendChart.update();
            }});

            // ---- Campaign Comparison ----
            const cmpData = {json.dumps(comparison)};
            const cmpCtx = document.getElementById('compareChart').getContext('2d');
            const cmpLabels = cmpData.campaigns.map(c => c.name);
            let currentMetric = 'spend';
            const compareChart = new Chart(cmpCtx, {{
                type: 'bar',
                data: {{
                    labels: cmpLabels,
                    datasets: [{{
                        label: 'Spend ($)',
                        data: cmpData.campaigns.map(c => c.spend),
                        backgroundColor: cmpData.campaigns.map((_, i) => COLORS[i % COLORS.length] + 'CC'),
                        borderColor: cmpData.campaigns.map((_, i) => COLORS[i % COLORS.length]),
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ x: {{ beginAtZero: true }} }}
                }}
            }});

            document.getElementById('compare-metrics').addEventListener('click', function(e) {{
                const btn = e.target.closest('.metric-btn');
                if (!btn) return;
                this.querySelectorAll('.metric-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const metric = btn.dataset.metric;
                const metricLabels = {{ spend: 'Spend ($)', impressions: 'Impressions', clicks: 'Clicks', ctr: 'CTR (%)', cpc: 'CPC ($)', conversions: 'Conversions' }};
                compareChart.data.datasets[0].data = cmpData.campaigns.map(c => c[metric]);
                compareChart.data.datasets[0].label = metricLabels[metric] || metric;
                compareChart.update();
            }});

            // ---- Spend Distribution Donut ----
            const spendData = {json.dumps(spend_dist)};
            new Chart(document.getElementById('spendDonut').getContext('2d'), {{
                type: 'doughnut',
                data: {{
                    labels: spendData.labels,
                    datasets: [{{
                        data: spendData.values,
                        backgroundColor: spendData.labels.map((_, i) => COLORS[i % COLORS.length] + 'CC'),
                        borderColor: '#fff',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, padding: 12 }} }},
                        tooltip: {{ callbacks: {{ label: function(ctx) {{ return ctx.label + ': $' + ctx.parsed.toLocaleString(); }} }} }}
                    }}
                }}
            }});

            // ---- Conversion Funnel (CSS) ----
            const funnel = {json.dumps(funnel)};
            const funnelStages = [
                {{ key: 'impressions', label: 'Impressions', color: COLORS[0] }},
                {{ key: 'clicks', label: 'Clicks', color: COLORS[1] }},
                {{ key: 'landing_page_clicks', label: 'Landing Page', color: COLORS[2] }},
                {{ key: 'conversions', label: 'Conversions', color: COLORS[3] }},
                {{ key: 'leads', label: 'Leads', color: COLORS[4] }}
            ];
            const funnelMax = funnel.impressions || 1;
            const funnelEl = document.getElementById('funnelContainer');
            funnelStages.forEach(function(s) {{
                const val = funnel[s.key] || 0;
                const pct = Math.max(2, val / funnelMax * 100);
                funnelEl.innerHTML += '<div class="funnel-bar">' +
                    '<div class="funnel-label">' + s.label + '</div>' +
                    '<div class="funnel-track"><div class="funnel-fill" style="width:' + pct + '%;background:' + s.color + '">' +
                    '</div></div>' +
                    '<div class="funnel-value">' + val.toLocaleString() + '</div></div>';
            }});

            // ---- Budget Utilization (CSS bars) ----
            const budgetItems = {json.dumps(budget)};
            const budgetEl = document.getElementById('budgetContainer');
            if (budgetItems.length === 0) {{
                budgetEl.innerHTML = '<p class="muted">No campaigns with daily budget data.</p>';
            }} else {{
                budgetItems.forEach(function(b) {{
                    const color = b.utilization > 95 ? '#c4483e' : b.utilization > 70 ? '#2d8a6e' : b.utilization > 40 ? '#d4940a' : '#a0aec0';
                    budgetEl.innerHTML += '<div class="budget-item">' +
                        '<div class="budget-name" title="' + b.name + '">' + b.name + '</div>' +
                        '<div class="budget-track"><div class="budget-fill" style="width:' + b.utilization + '%;background:' + color + '"></div></div>' +
                        '<div class="budget-pct">' + b.utilization + '%</div></div>';
                }});
            }}

            // ---- Engagement Radar ----
            const radarData = {json.dumps(radar)};
            if (radarData.campaigns.length > 0) {{
                new Chart(document.getElementById('radarChart').getContext('2d'), {{
                    type: 'radar',
                    data: {{
                        labels: ['CTR', 'Engagement Rate', 'Social Rate', 'Conversion Rate', 'CPC Efficiency'],
                        datasets: radarData.campaigns.map(function(c, i) {{
                            return {{
                                label: c.name,
                                data: [c.ctr, c.engagement_rate, c.social_rate, c.conversion_rate, c.cpc_efficiency],
                                borderColor: COLORS[i % COLORS.length],
                                backgroundColor: COLORS[i % COLORS.length] + '20',
                                pointBackgroundColor: COLORS[i % COLORS.length],
                                borderWidth: 2
                            }};
                        }})
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 10 }}, padding: 8 }} }} }},
                        scales: {{ r: {{ beginAtZero: true, ticks: {{ font: {{ size: 9 }} }} }} }}
                    }}
                }});
            }} else {{
                document.getElementById('radarChart').parentElement.innerHTML = '<p class="muted">Not enough campaign data for radar chart.</p>';
            }}

            // ---- Creative Performance ----
            const crData = {json.dumps(creatives)};
            if (crData.creatives.length > 0) {{
                new Chart(document.getElementById('creativeChart').getContext('2d'), {{
                    type: 'bar',
                    data: {{
                        labels: crData.creatives.map(c => c.label),
                        datasets: [
                            {{ label: 'Impressions', data: crData.creatives.map(c => c.impressions), backgroundColor: COLORS[0] + 'AA' }},
                            {{ label: 'Clicks', data: crData.creatives.map(c => c.clicks), backgroundColor: COLORS[1] + 'AA' }}
                        ]
                    }},
                    options: {{
                        indexAxis: 'y',
                        responsive: true,
                        plugins: {{ legend: {{ position: 'top', labels: {{ font: {{ size: 10 }} }} }} }},
                        scales: {{ x: {{ beginAtZero: true }} }}
                    }}
                }});
            }} else {{
                document.getElementById('creativeChart').parentElement.innerHTML = '<p class="muted">No creative performance data available.</p>';
            }}

            // ---- Demographics ----
            const demoData = {json.dumps(demographics)};
            const demoContainer = document.getElementById('demoCharts');
            const demoKeys = Object.keys(demoData);
            if (demoKeys.length === 0) {{
                demoContainer.innerHTML = '<div class="chart-card full-width"><p class="muted">No demographic data available. Run a sync to fetch audience data.</p></div>';
            }}
            demoKeys.forEach(function(key, idx) {{
                const d = demoData[key];
                const card = document.createElement('div');
                card.className = 'chart-card';
                card.innerHTML = '<h3>' + d.label + '</h3><div class="chart-container"><canvas id="demo_' + key + '"></canvas></div>';
                demoContainer.appendChild(card);
                new Chart(document.getElementById('demo_' + key).getContext('2d'), {{
                    type: 'bar',
                    data: {{
                        labels: d.segments,
                        datasets: [{{
                            label: 'Impressions',
                            data: d.impressions,
                            backgroundColor: COLORS[idx % COLORS.length] + 'AA',
                            borderColor: COLORS[idx % COLORS.length],
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        responsive: true,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ x: {{ beginAtZero: true }} }}
                    }}
                }});
            }});
        }})();
        </script>
        """

        return _render(html, page_title="Visual Dashboard", active_page="visual")

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
