"""Fetchers for LinkedIn Ads analytics and demographic data.

Handles the ``/adAnalytics`` endpoint with different pivots (CAMPAIGN,
CREATIVE, and MEMBER_* demographic pivots).  Batches campaign URNs in
groups of 20 to avoid URL-length limits.
"""

from __future__ import annotations

import datetime

from linkedin_action_center.ingestion.client import LinkedInClient

# Metrics requested on every analytics call
CORE_METRICS = [
    "impressions",
    "clicks",
    "costInLocalCurrency",
    "landingPageClicks",
    "externalWebsiteConversions",
    "likes",
    "comments",
    "shares",
    "follows",
    "oneClickLeads",
    "opens",
    "sends",
]

FIELDS_PARAM = ",".join(CORE_METRICS + ["dateRange", "pivotValues"])

# Demographic pivots of interest
DEMOGRAPHIC_PIVOTS = [
    "MEMBER_JOB_TITLE",
    "MEMBER_JOB_FUNCTION",
    "MEMBER_INDUSTRY",
    "MEMBER_SENIORITY",
    "MEMBER_COMPANY_SIZE",
    "MEMBER_COUNTRY_V2",
]

DEMO_FIELDS = "impressions,clicks,costInLocalCurrency,pivotValues"

# Batch size for campaign-URN lists to avoid URL-length problems
_BATCH_SIZE = 20


# -- Helpers ----------------------------------------------------------------

def _date_range_param(
    start: datetime.date,
    end: datetime.date,
) -> str:
    """Build LinkedIn's ``dateRange`` query-string value."""
    return (
        f"(start:(year:{start.year},month:{start.month},day:{start.day}),"
        f"end:(year:{end.year},month:{end.month},day:{end.day}))"
    )


def _campaign_urns(campaign_ids: list[int]) -> str:
    return ",".join(
        f"urn%3Ali%3AsponsoredCampaign%3A{cid}" for cid in campaign_ids
    )


# -- Analytics fetchers -----------------------------------------------------

def fetch_campaign_metrics(
    client: LinkedInClient,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date,
    granularity: str = "DAILY",
) -> list[dict]:
    """
    Fetch performance metrics pivoted by CAMPAIGN.

    Parameters
    ----------
    granularity : ``"DAILY"`` for time-series or ``"ALL"`` for a single
        aggregate row per campaign.
    """
    if not campaign_ids:
        return []

    all_rows: list[dict] = []
    for i in range(0, len(campaign_ids), _BATCH_SIZE):
        batch = campaign_ids[i : i + _BATCH_SIZE]
        params = (
            f"q=analytics"
            f"&pivot=CAMPAIGN"
            f"&timeGranularity={granularity}"
            f"&dateRange={_date_range_param(start, end)}"
            f"&campaigns=List({_campaign_urns(batch)})"
            f"&fields={FIELDS_PARAM}"
        )
        data = client.get("/adAnalytics", params)
        all_rows.extend(data.get("elements", []))

    return all_rows


def fetch_creative_metrics(
    client: LinkedInClient,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date,
    granularity: str = "DAILY",
) -> list[dict]:
    """Fetch performance metrics pivoted by CREATIVE."""
    if not campaign_ids:
        return []

    all_rows: list[dict] = []
    for i in range(0, len(campaign_ids), _BATCH_SIZE):
        batch = campaign_ids[i : i + _BATCH_SIZE]
        params = (
            f"q=analytics"
            f"&pivot=CREATIVE"
            f"&timeGranularity={granularity}"
            f"&dateRange={_date_range_param(start, end)}"
            f"&campaigns=List({_campaign_urns(batch)})"
            f"&fields={FIELDS_PARAM}"
        )
        data = client.get("/adAnalytics", params)
        all_rows.extend(data.get("elements", []))

    return all_rows


def fetch_demographics(
    client: LinkedInClient,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date,
    pivots: list[str] | None = None,
) -> dict[str, list[dict]]:
    """
    Fetch audience demographic breakdowns (aggregate, not daily).

    Returns a dict mapping pivot name to its list of rows.  Failures on
    individual pivots are captured as empty lists rather than raising.
    """
    if not campaign_ids:
        return {}

    if pivots is None:
        pivots = DEMOGRAPHIC_PIVOTS

    urns = _campaign_urns(campaign_ids)
    demographics: dict[str, list[dict]] = {}

    for pivot in pivots:
        params = (
            f"q=analytics"
            f"&pivot={pivot}"
            f"&timeGranularity=ALL"
            f"&dateRange={_date_range_param(start, end)}"
            f"&campaigns=List({urns})"
            f"&fields={DEMO_FIELDS}"
        )
        try:
            data = client.get("/adAnalytics", params)
            demographics[pivot] = data.get("elements", [])
        except Exception:
            demographics[pivot] = []

    return demographics


def _extract_urn_parts(urn: str) -> tuple[str, str]:
    """Extract (entity_type, entity_id) from a URN like 'urn:li:title:1335'."""
    parts = str(urn).split(":")
    if len(parts) >= 4:
        return parts[2], parts[3]
    return "", ""


def resolve_demographic_urns(
    client: LinkedInClient,
    demo_data: dict[str, list[dict]],
) -> dict[str, str]:
    """
    Resolve demographic URNs to human-readable names.

    Groups URNs by entity type and uses the appropriate LinkedIn API
    endpoint for each type.  Falls back gracefully on failures.
    """
    # Collect all unique URNs grouped by entity type
    urns_by_type: dict[str, list[str]] = {}
    for _pivot, rows in demo_data.items():
        for r in rows:
            for pv in r.get("pivotValues", []):
                pv_str = str(pv)
                if "urn:" not in pv_str:
                    continue
                etype, eid = _extract_urn_parts(pv_str)
                if etype and eid:
                    urns_by_type.setdefault(etype, []).append(pv_str)

    if not urns_by_type:
        return {}

    urn_to_name: dict[str, str] = {}

    # Map entity types to their LinkedIn batch-GET endpoints
    # These endpoints accept: /endpoint?ids=List(id1,id2,...)
    type_to_endpoint = {
        "title": "/adTargetingEntities",
        "industry": "/adTargetingEntities",
        "geo": "/adTargetingEntities",
        "country": "/adTargetingEntities",
        "region": "/adTargetingEntities",
    }

    # Try the general /adTargetingEntities batch approach first for all URNs
    all_urns = list({u for urns in urns_by_type.values() for u in urns})
    for i in range(0, len(all_urns), 50):
        batch = all_urns[i : i + 50]
        encoded = ",".join(u.replace(":", "%3A") for u in batch)
        # Try the facetUrn-based query which is more reliable
        for query_style in [
            f"q=urns&urns=List({encoded})",
            f"q=adTargetingFacet&urns=List({encoded})",
        ]:
            try:
                data = client.get("/adTargetingEntities", query_style)
                for elem in data.get("elements", []):
                    urn = elem.get("urn", "")
                    name = elem.get("name", "") or elem.get("facetName", "")
                    if urn and name:
                        urn_to_name[urn] = name
                if urn_to_name:
                    break  # first style worked
            except Exception:
                continue

    return urn_to_name
