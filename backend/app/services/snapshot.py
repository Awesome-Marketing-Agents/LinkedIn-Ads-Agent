"""Snapshot assembly: transform raw API data into a structured dict.

This is the same logic from the original ``storage/snapshot.py`` but
with updated imports for the new package layout.
"""

from __future__ import annotations

import datetime as _dt
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.models.linkedin_api import (
    LinkedInAccount,
    LinkedInAnalyticsRow,
    LinkedInCampaign,
    LinkedInCreative,
    LinkedInDemographicRow,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _extract_id_from_urn(urn: str) -> str:
    return urn.split(":")[-1] if ":" in str(urn) else str(urn)


def _aggregate_metrics(rows: list[dict]) -> dict:
    agg = {
        "impressions": 0, "clicks": 0, "spend": 0.0,
        "landing_page_clicks": 0, "conversions": 0,
        "likes": 0, "comments": 0, "shares": 0,
        "follows": 0, "leads": 0, "opens": 0, "sends": 0,
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

    imp, clk, spend, conv = agg["impressions"], agg["clicks"], agg["spend"], agg["conversions"]
    agg["ctr"] = round(clk / imp * 100, 4) if imp else 0
    agg["cpc"] = round(spend / clk, 2) if clk else 0
    agg["cpm"] = round(spend / imp * 1000, 2) if imp else 0
    agg["cpl"] = round(spend / conv, 2) if conv else 0
    agg["spend"] = round(spend, 2)
    return agg


def _daily_time_series(rows: list[dict]) -> list[dict]:
    daily: dict[str, dict] = {}
    for r in rows:
        dr = r.get("dateRange", {})
        start = dr.get("start", {})
        date_key = f"{start.get('year', 0)}-{start.get('month', 0):02d}-{start.get('day', 0):02d}"
        if date_key not in daily:
            daily[date_key] = {
                "date": date_key, "impressions": 0, "clicks": 0, "spend": 0.0,
                "landing_page_clicks": 0, "conversions": 0,
                "likes": 0, "comments": 0, "shares": 0,
                "follows": 0, "leads": 0, "opens": 0, "sends": 0,
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
        imp, clk = d["impressions"], d["clicks"]
        d["ctr"] = round(clk / imp * 100, 4) if imp else 0
        d["cpc"] = round(d["spend"] / clk, 2) if clk else 0
        result.append(d)
    return result


_SENIORITY_MAP = {
    "1": "Unpaid", "2": "Training", "3": "Entry", "4": "Senior",
    "5": "Manager", "6": "Director", "7": "VP", "8": "CXO",
    "9": "Partner", "10": "Owner",
}
_COMPANY_SIZE_MAP = {
    "A": "Self-employed (1)", "B": "2-10 employees", "C": "11-50 employees",
    "D": "51-200 employees", "E": "201-500 employees", "F": "501-1,000 employees",
    "G": "1,001-5,000 employees", "H": "5,001-10,000 employees", "I": "10,001+ employees",
}
_JOB_FUNCTION_MAP = {
    "1": "Accounting", "2": "Administrative", "3": "Arts and Design",
    "4": "Business Development", "5": "Community & Social Services", "6": "Consulting",
    "7": "Education", "8": "Engineering", "9": "Entrepreneurship", "10": "Finance",
    "11": "Healthcare Services", "12": "Human Resources", "13": "Information Technology",
    "14": "Legal", "15": "Marketing", "16": "Media & Communications",
    "17": "Military & Protective Services", "18": "Operations", "19": "Product Management",
    "20": "Program & Project Management", "21": "Purchasing", "22": "Quality Assurance",
    "23": "Real Estate", "24": "Research", "25": "Sales", "26": "Customer Success & Support",
}


def _resolve_urn_locally(urn: str) -> str:
    parts = str(urn).split(":")
    if len(parts) < 4:
        return ""
    entity_type, entity_id = parts[2], parts[3]
    if entity_type == "seniority":
        return _SENIORITY_MAP.get(entity_id, "")
    if entity_type in ("companySizeRange", "companySize"):
        return _COMPANY_SIZE_MAP.get(entity_id, "")
    if entity_type == "function":
        return _JOB_FUNCTION_MAP.get(entity_id, "")
    return ""


def _top_demographics(
    demo_rows: list[dict], urn_names: dict[str, str] | None = None, top_n: int = 10,
) -> list[dict]:
    if urn_names is None:
        urn_names = {}
    sorted_rows = sorted(demo_rows, key=lambda r: r.get("impressions", 0), reverse=True)
    total_imp = sum(r.get("impressions", 0) for r in sorted_rows)
    result = []
    for r in sorted_rows[:top_n]:
        imp, clk = r.get("impressions", 0), r.get("clicks", 0)
        raw_segment = r.get("pivotValues", ["?"])[0]
        resolved = urn_names.get(raw_segment, "") or _resolve_urn_locally(raw_segment)
        result.append({
            "segment": resolved or raw_segment,
            "segment_urn": raw_segment,
            "impressions": imp,
            "clicks": clk,
            "ctr": round(clk / imp * 100, 2) if imp else 0,
            "share_of_impressions": round(imp / total_imp * 100, 1) if total_imp else 0,
        })
    return result


def _validate_list(raw_items: list[dict], model_cls: type, label: str) -> list[dict]:
    valid: list[dict] = []
    for raw in raw_items:
        try:
            model_cls.model_validate(raw)
            valid.append(raw)
        except ValidationError as exc:
            item_id = raw.get("id", "unknown")
            logger.warning("Validation failed for %s %s: %d error(s) - skipped", label, item_id, exc.error_count())
    return valid


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
    accounts = _validate_list(accounts, LinkedInAccount, "account")
    campaigns_list = _validate_list(campaigns_list, LinkedInCampaign, "campaign")
    creatives_list = _validate_list(creatives_list, LinkedInCreative, "creative")
    camp_metrics = _validate_list(camp_metrics, LinkedInAnalyticsRow, "campaign_metric")
    creat_metrics = _validate_list(creat_metrics, LinkedInAnalyticsRow, "creative_metric")

    validated_demo: dict = {}
    if isinstance(demo_data, dict):
        for pivot, rows in demo_data.items():
            if isinstance(rows, list):
                validated_demo[pivot] = _validate_list(rows, LinkedInDemographicRow, f"demographic[{pivot}]")
            else:
                validated_demo[pivot] = rows
        demo_data = validated_demo

    camp_metric_map: dict[str, list[dict]] = {}
    for r in camp_metrics:
        for pv in r.get("pivotValues", []):
            cid = _extract_id_from_urn(pv)
            camp_metric_map.setdefault(cid, []).append(r)

    creat_metric_map: dict[str, list[dict]] = {}
    for r in creat_metrics:
        for pv in r.get("pivotValues", []):
            if "sponsoredCreative" in str(pv):
                creat_metric_map.setdefault(pv, []).append(r)

    creatives_by_campaign: dict[str, list[dict]] = {}
    for cr in creatives_list:
        camp_urn = cr.get("campaign", "")
        creatives_by_campaign.setdefault(camp_urn, []).append(cr)

    campaigns_by_account: dict[int, list[dict]] = {}
    for camp in campaigns_list:
        acct_id = camp.get("_account_id")
        if acct_id is not None:
            try:
                campaigns_by_account.setdefault(int(acct_id), []).append(camp)
            except (ValueError, TypeError):
                pass

    snapshot: dict = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "date_range": {"start": str(date_start), "end": str(date_end), "days": (date_end - date_start).days},
        "accounts": [],
    }

    for acct in accounts:
        acct_snapshot = {
            "id": acct.get("id"), "name": acct.get("name"), "status": acct.get("status"),
            "currency": acct.get("currency"), "type": acct.get("type"),
            "test": acct.get("test", False), "created_at": acct.get("createdAt"),
            "campaigns": [], "audience_demographics": {},
        }
        acct_id = acct.get("id")
        acct_campaigns = campaigns_by_account.get(acct_id) if acct_id is not None else None
        if acct_campaigns is None:
            acct_campaigns = campaigns_list

        for camp in acct_campaigns:
            camp_id = str(camp.get("id", ""))
            camp_urn = f"urn:li:sponsoredCampaign:{camp_id}"
            budget = camp.get("dailyBudget", {})
            total_budget = camp.get("totalBudget", {})
            unit_cost = camp.get("unitCost", {})

            camp_snapshot = {
                "id": camp.get("id"), "name": camp.get("name"),
                "status": camp.get("status"), "type": camp.get("type"),
                "created_at": camp.get("createdAt"),
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
                "metrics_summary": {}, "daily_metrics": [], "creatives": [],
            }

            camp_rows = camp_metric_map.get(camp_id, [])
            if camp_rows:
                camp_snapshot["metrics_summary"] = _aggregate_metrics(camp_rows)
                camp_snapshot["daily_metrics"] = _daily_time_series(camp_rows)

            for cr in creatives_by_campaign.get(camp_urn, []):
                cr_id = cr.get("id", "")
                cr_snapshot = {
                    "id": cr_id, "intended_status": cr.get("intendedStatus"),
                    "is_serving": cr.get("isServing", False),
                    "serving_hold_reasons": cr.get("servingHoldReasons", []),
                    "content_reference": cr.get("content", {}).get("reference"),
                    "created_at": cr.get("createdAt"), "last_modified_at": cr.get("lastModifiedAt"),
                    "metrics_summary": {}, "daily_metrics": [],
                }
                cr_rows = creat_metric_map.get(cr_id, [])
                if cr_rows:
                    cr_snapshot["metrics_summary"] = _aggregate_metrics(cr_rows)
                    cr_snapshot["daily_metrics"] = _daily_time_series(cr_rows)
                camp_snapshot["creatives"].append(cr_snapshot)

            acct_snapshot["campaigns"].append(camp_snapshot)

        acct_demo_raw = None
        urn_names: dict[str, str] = {}
        if isinstance(demo_data, dict) and acct_id in demo_data:
            entry = demo_data.get(acct_id, {})
            if isinstance(entry, dict) and "pivots" in entry:
                acct_demo_raw = entry.get("pivots", {})
                urn_names = entry.get("urn_names", {})
            elif isinstance(entry, dict):
                acct_demo_raw = entry
        elif isinstance(demo_data, dict):
            acct_demo_raw = demo_data

        if isinstance(acct_demo_raw, dict):
            for pivot, rows in acct_demo_raw.items():
                key = str(pivot).lower().replace("member_", "")
                acct_snapshot["audience_demographics"][key] = _top_demographics(rows or [], urn_names=urn_names)

        snapshot["accounts"].append(acct_snapshot)

    return snapshot


def save_snapshot_json(snap: dict, path: Path | None = None) -> Path:
    if path is None:
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snapshots_dir = Path("data/snapshots")
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        path = snapshots_dir / f"snapshot_{ts}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, indent=2, default=str))
    return path
