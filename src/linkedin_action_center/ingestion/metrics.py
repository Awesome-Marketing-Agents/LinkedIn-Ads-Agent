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
