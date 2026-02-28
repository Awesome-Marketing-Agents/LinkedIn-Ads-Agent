"""Snapshot assembly: transform raw API data into a structured dict for LLM analysis.

Also handles writing the snapshot to JSON on disk.
Raw API data is validated through Pydantic models before processing;
invalid records are logged and skipped.
"""

from __future__ import annotations

import json
import datetime as _dt
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from linkedin_action_center.core.config import SNAPSHOT_DIR
from linkedin_action_center.models.api_models import (
    LinkedInAccount,
    LinkedInCampaign,
    LinkedInCreative,
    LinkedInAnalyticsRow,
    LinkedInDemographicRow,
)
from linkedin_action_center.utils.logger import logger


# -- Internal helpers --------------------------------------------------------

def _extract_id_from_urn(urn: str) -> str:
    """Extract the trailing numeric ID from a LinkedIn URN string."""
    return urn.split(":")[-1] if ":" in str(urn) else str(urn)


def _aggregate_metrics(rows: list[dict]) -> dict:
    """Sum core metrics across *rows* and compute derived ratios."""
    agg = {
        "impressions": 0,
        "clicks": 0,
        "spend": 0.0,
        "landing_page_clicks": 0,
        "conversions": 0,
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "follows": 0,
        "leads": 0,
        "opens": 0,
        "sends": 0,
    }
    for r in rows:
        agg["impressions"] += r.get("impressions", 0)
        agg["clicks"] += r.get("clicks", 0)
        agg["spend"] += float(r.get("costInLocalCurrency", "0") or "0")
        agg["landing_page_clicks"] += r.get("landingPageClicks", 0)
        agg["conversions"] += r.get("externalWebsiteConversions", 0)
        agg["likes"] += r.get("likes", 0)
        agg["comments"] += r.get("comments", 0)
        agg["shares"] += r.get("shares", 0)
        agg["follows"] += r.get("follows", 0)
        agg["leads"] += r.get("oneClickLeads", 0)
        agg["opens"] += r.get("opens", 0)
        agg["sends"] += r.get("sends", 0)

    imp = agg["impressions"]
    clk = agg["clicks"]
    spend = agg["spend"]
    conv = agg["conversions"]

    agg["ctr"] = round(clk / imp * 100, 4) if imp else 0
    agg["cpc"] = round(spend / clk, 2) if clk else 0
    agg["cpm"] = round(spend / imp * 1000, 2) if imp else 0
    agg["cpl"] = round(spend / conv, 2) if conv else 0
    agg["spend"] = round(spend, 2)

    return agg


def _daily_time_series(rows: list[dict]) -> list[dict]:
    """Collapse metric rows into a date-sorted daily time series."""
    daily: dict[str, dict] = {}
    for r in rows:
        dr = r.get("dateRange", {})
        start = dr.get("start", {})
        date_key = (
            f"{start.get('year', 0)}-{start.get('month', 0):02d}-"
            f"{start.get('day', 0):02d}"
        )
        if date_key not in daily:
            daily[date_key] = {
                "date": date_key,
                "impressions": 0,
                "clicks": 0,
                "spend": 0.0,
                "landing_page_clicks": 0,
                "conversions": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "follows": 0,
                "leads": 0,
                "opens": 0,
                "sends": 0,
            }
        d = daily[date_key]
        d["impressions"] += r.get("impressions", 0)
        d["clicks"] += r.get("clicks", 0)
        d["spend"] += float(r.get("costInLocalCurrency", "0") or "0")
        d["landing_page_clicks"] += r.get("landingPageClicks", 0)
        d["conversions"] += r.get("externalWebsiteConversions", 0)
        d["likes"] += r.get("likes", 0)
        d["comments"] += r.get("comments", 0)
        d["shares"] += r.get("shares", 0)
        d["follows"] += r.get("follows", 0)
        d["leads"] += r.get("oneClickLeads", 0)
        d["opens"] += r.get("opens", 0)
        d["sends"] += r.get("sends", 0)

    result = []
    for d in sorted(daily.values(), key=lambda x: x["date"]):
        d["spend"] = round(d["spend"], 2)
        imp = d["impressions"]
        clk = d["clicks"]
        d["ctr"] = round(clk / imp * 100, 4) if imp else 0
        d["cpc"] = round(d["spend"] / clk, 2) if clk else 0
        result.append(d)
    return result


# -- Well-known LinkedIn enum lookups ----------------------------------------
# These are static mappings for entity types where LinkedIn uses fixed numeric
# IDs.  They never change, so we can resolve them locally without an API call.

_SENIORITY_MAP = {
    "1": "Unpaid",
    "2": "Training",
    "3": "Entry",
    "4": "Senior",
    "5": "Manager",
    "6": "Director",
    "7": "VP",
    "8": "CXO",
    "9": "Partner",
    "10": "Owner",
}

_COMPANY_SIZE_MAP = {
    "A": "Self-employed (1)",
    "B": "2–10 employees",
    "C": "11–50 employees",
    "D": "51–200 employees",
    "E": "201–500 employees",
    "F": "501–1,000 employees",
    "G": "1,001–5,000 employees",
    "H": "5,001–10,000 employees",
    "I": "10,001+ employees",
}

_JOB_FUNCTION_MAP = {
    "1": "Accounting",
    "2": "Administrative",
    "3": "Arts and Design",
    "4": "Business Development",
    "5": "Community & Social Services",
    "6": "Consulting",
    "7": "Education",
    "8": "Engineering",
    "9": "Entrepreneurship",
    "10": "Finance",
    "11": "Healthcare Services",
    "12": "Human Resources",
    "13": "Information Technology",
    "14": "Legal",
    "15": "Marketing",
    "16": "Media & Communications",
    "17": "Military & Protective Services",
    "18": "Operations",
    "19": "Product Management",
    "20": "Program & Project Management",
    "21": "Purchasing",
    "22": "Quality Assurance",
    "23": "Real Estate",
    "24": "Research",
    "25": "Sales",
    "26": "Customer Success & Support",
}


def _resolve_urn_locally(urn: str) -> str:
    """Best-effort local resolution of a LinkedIn URN to a human name."""
    s = str(urn)
    # Extract the type and ID from URNs like "urn:li:seniority:6"
    parts = s.split(":")
    if len(parts) < 4:
        return ""
    entity_type = parts[2]
    entity_id = parts[3]

    if entity_type == "seniority":
        return _SENIORITY_MAP.get(entity_id, "")
    if entity_type == "companySizeRange" or entity_type == "companySize":
        return _COMPANY_SIZE_MAP.get(entity_id, "")
    if entity_type == "function":
        return _JOB_FUNCTION_MAP.get(entity_id, "")
    return ""


def _top_demographics(
    demo_rows: list[dict],
    urn_names: dict[str, str] | None = None,
    top_n: int = 10,
) -> list[dict]:
    """Return the *top_n* demographic segments ranked by impressions."""
    if urn_names is None:
        urn_names = {}
    sorted_rows = sorted(
        demo_rows, key=lambda r: r.get("impressions", 0), reverse=True,
    )
    total_imp = sum(r.get("impressions", 0) for r in sorted_rows)
    result = []
    for r in sorted_rows[:top_n]:
        imp = r.get("impressions", 0)
        clk = r.get("clicks", 0)
        raw_segment = r.get("pivotValues", ["?"])[0]
        # Try API-resolved name first, then local enum lookup, then raw URN
        resolved_name = urn_names.get(raw_segment, "") or _resolve_urn_locally(raw_segment)
        result.append({
            "segment": resolved_name or raw_segment,
            "segment_urn": raw_segment,
            "impressions": imp,
            "clicks": clk,
            "ctr": round(clk / imp * 100, 2) if imp else 0,
            "share_of_impressions": round(imp / total_imp * 100, 1) if total_imp else 0,
        })
    return result


# -- Validation helpers -----------------------------------------------------

def _validate_list(raw_items: list[dict], model_cls: type, label: str) -> list[dict]:
    """Validate a list of raw dicts through *model_cls*.

    Returns the original dicts for items that pass validation (preserving all
    original keys for downstream processing).  Invalid items are logged and
    skipped.
    """
    valid: list[dict] = []
    for raw in raw_items:
        try:
            model_cls.model_validate(raw)
            valid.append(raw)
        except ValidationError as exc:
            item_id = raw.get("id", "unknown")
            logger.warning(
                f"Validation failed for {label} {item_id}: {exc.error_count()} error(s) — skipped"
            )
    return valid


# -- Public API --------------------------------------------------------------

def assemble_snapshot(
    accounts: list[dict],
    campaigns_list: list[dict],
    creatives_list: list[dict],
    camp_metrics: list[dict],
    creat_metrics: list[dict],
    demo_data: dict,
    date_start: _dt.date,
    date_end: _dt.date,
) -> dict:
    """
    Combine all raw API data into a single structured snapshot.

    Raw data is validated through Pydantic models before processing.
    Invalid records are logged and skipped.
    """
    # --- Validation gate ---------------------------------------------------
    accounts = _validate_list(accounts, LinkedInAccount, "account")
    campaigns_list = _validate_list(campaigns_list, LinkedInCampaign, "campaign")
    creatives_list = _validate_list(creatives_list, LinkedInCreative, "creative")
    camp_metrics = _validate_list(camp_metrics, LinkedInAnalyticsRow, "campaign_metric")
    creat_metrics = _validate_list(creat_metrics, LinkedInAnalyticsRow, "creative_metric")

    # Validate demographic rows per pivot
    validated_demo: dict = {}
    if isinstance(demo_data, dict):
        for pivot, rows in demo_data.items():
            if isinstance(rows, list):
                validated_demo[pivot] = _validate_list(
                    rows, LinkedInDemographicRow, f"demographic[{pivot}]",
                )
            else:
                validated_demo[pivot] = rows
        demo_data = validated_demo

    # --- Index building (unchanged logic) ---------------------------------
    # Index campaign metrics by campaign ID
    camp_metric_map: dict[str, list[dict]] = {}
    for r in camp_metrics:
        for pv in r.get("pivotValues", []):
            cid = _extract_id_from_urn(pv)
            camp_metric_map.setdefault(cid, []).append(r)

    # Index creative metrics by creative URN
    creat_metric_map: dict[str, list[dict]] = {}
    for r in creat_metrics:
        for pv in r.get("pivotValues", []):
            if "sponsoredCreative" in str(pv):
                creat_metric_map.setdefault(pv, []).append(r)

    # Index creatives by campaign URN
    creatives_by_campaign: dict[str, list[dict]] = {}
    for cr in creatives_list:
        camp_urn = cr.get("campaign", "")
        creatives_by_campaign.setdefault(camp_urn, []).append(cr)

    # Index campaigns by account (if caller provided _account_id tags)
    campaigns_by_account_id: dict[int, list[dict]] = {}
    for camp in campaigns_list:
        acct_id = camp.get("_account_id")
        if acct_id is None:
            continue
        try:
            acct_id_int = int(acct_id)
        except Exception:
            continue
        campaigns_by_account_id.setdefault(acct_id_int, []).append(camp)

    snapshot: dict = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "date_range": {
            "start": str(date_start),
            "end": str(date_end),
            "days": (date_end - date_start).days,
        },
        "accounts": [],
    }

    for acct in accounts:
        acct_snapshot = {
            "id": acct.get("id"),
            "name": acct.get("name"),
            "status": acct.get("status"),
            "currency": acct.get("currency"),
            "type": acct.get("type"),
            "test": acct.get("test", False),
            "campaigns": [],
            "audience_demographics": {},
        }

        acct_id = acct.get("id")
        acct_campaigns = campaigns_by_account_id.get(acct_id) if acct_id is not None else None
        if acct_campaigns is None:
            # Backwards compatibility: if caller didn't tag campaigns, include everything.
            acct_campaigns = campaigns_list

        for camp in acct_campaigns:
            camp_id = str(camp.get("id", ""))
            camp_urn = f"urn:li:sponsoredCampaign:{camp_id}"

            budget = camp.get("dailyBudget", {})
            total_budget = camp.get("totalBudget", {})
            unit_cost = camp.get("unitCost", {})

            camp_snapshot = {
                "id": camp.get("id"),
                "name": camp.get("name"),
                "status": camp.get("status"),
                "type": camp.get("type"),
                "settings": {
                    "daily_budget": budget.get("amount") if budget else None,
                    "daily_budget_currency": budget.get("currencyCode") if budget else None,
                    "total_budget": total_budget.get("amount") if total_budget else None,
                    "cost_type": camp.get("costType"),
                    "unit_cost": unit_cost.get("amount") if unit_cost else None,
                    "bid_strategy": camp.get("optimizationTargetType"),
                    "creative_selection": camp.get("creativeSelection"),
                    "offsite_delivery_enabled": camp.get("offsiteDeliveryEnabled", False),
                    "audience_expansion_enabled": camp.get("audienceExpansionEnabled", False),
                    "run_schedule": camp.get("runSchedule"),
                    "campaign_group": camp.get("campaignGroup"),
                },
                "metrics_summary": {},
                "daily_metrics": [],
                "creatives": [],
            }

            # Aggregate campaign metrics
            camp_rows = camp_metric_map.get(camp_id, [])
            if camp_rows:
                camp_snapshot["metrics_summary"] = _aggregate_metrics(camp_rows)
                camp_snapshot["daily_metrics"] = _daily_time_series(camp_rows)

            # Attach creatives and their metrics
            for cr in creatives_by_campaign.get(camp_urn, []):
                cr_id = cr.get("id", "")
                cr_snapshot = {
                    "id": cr_id,
                    "intended_status": cr.get("intendedStatus"),
                    "is_serving": cr.get("isServing", False),
                    "serving_hold_reasons": cr.get("servingHoldReasons", []),
                    "content_reference": cr.get("content", {}).get("reference"),
                    "created_at": cr.get("createdAt"),
                    "last_modified_at": cr.get("lastModifiedAt"),
                    "metrics_summary": {},
                }
                cr_rows = creat_metric_map.get(cr_id, [])
                if cr_rows:
                    cr_snapshot["metrics_summary"] = _aggregate_metrics(cr_rows)
                camp_snapshot["creatives"].append(cr_snapshot)

            acct_snapshot["campaigns"].append(camp_snapshot)

        # Audience demographics
        acct_demo_raw = None
        urn_names: dict[str, str] = {}
        if isinstance(demo_data, dict) and acct_id in demo_data:
            entry = demo_data.get(acct_id, {})
            if isinstance(entry, dict) and "pivots" in entry:
                # New format: {"pivots": {...}, "urn_names": {...}}
                acct_demo_raw = entry.get("pivots", {})
                urn_names = entry.get("urn_names", {})
            elif isinstance(entry, dict):
                acct_demo_raw = entry
        elif isinstance(demo_data, dict):
            # Backwards compatibility: a single dict[pivot -> rows] reused for all accounts
            acct_demo_raw = demo_data

        if isinstance(acct_demo_raw, dict):
            for pivot, rows in acct_demo_raw.items():
                key = str(pivot).lower().replace("member_", "")
                acct_snapshot["audience_demographics"][key] = _top_demographics(
                    rows or [], urn_names=urn_names,
                )

        snapshot["accounts"].append(acct_snapshot)

    return snapshot


def save_snapshot_json(snap: dict, path: Path | None = None) -> Path:
    """Write *snap* to a JSON file and return the path."""
    if path is None:
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = SNAPSHOT_DIR / f"snapshot_{ts}.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, indent=2, default=str))
    return path
