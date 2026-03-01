"""Async analytics and demographics fetchers with parallel batch support."""

from __future__ import annotations

import asyncio
import datetime

from app.linkedin.client import LinkedInClient
from app.utils.logging import get_logger

logger = get_logger(__name__)

CORE_METRICS = [
    "impressions", "clicks", "costInLocalCurrency", "landingPageClicks",
    "externalWebsiteConversions", "likes", "comments", "shares",
    "follows", "oneClickLeads", "opens", "sends",
]
FIELDS_PARAM = ",".join(CORE_METRICS + ["dateRange", "pivotValues"])

DEMOGRAPHIC_PIVOTS = [
    "MEMBER_JOB_TITLE", "MEMBER_JOB_FUNCTION", "MEMBER_INDUSTRY",
    "MEMBER_SENIORITY", "MEMBER_COMPANY_SIZE", "MEMBER_COUNTRY_V2",
]
DEMO_FIELDS = "impressions,clicks,costInLocalCurrency,pivotValues"

_BATCH_SIZE = 20


def _date_range_param(start: datetime.date, end: datetime.date) -> str:
    return (
        f"(start:(year:{start.year},month:{start.month},day:{start.day}),"
        f"end:(year:{end.year},month:{end.month},day:{end.day}))"
    )


def _campaign_urns(campaign_ids: list[int]) -> str:
    return ",".join(f"urn%3Ali%3AsponsoredCampaign%3A{cid}" for cid in campaign_ids)


async def _fetch_metrics_batch(
    client: LinkedInClient,
    batch: list[int],
    start: datetime.date,
    end: datetime.date,
    pivot: str,
    granularity: str,
) -> list[dict]:
    fields = FIELDS_PARAM if pivot in ("CAMPAIGN", "CREATIVE") else DEMO_FIELDS
    params = (
        f"q=analytics&pivot={pivot}&timeGranularity={granularity}"
        f"&dateRange={_date_range_param(start, end)}"
        f"&campaigns=List({_campaign_urns(batch)})"
        f"&fields={fields}"
    )
    data = await client.get("/adAnalytics", params)
    return data.get("elements", [])


async def fetch_campaign_metrics(
    client: LinkedInClient,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date,
    granularity: str = "DAILY",
) -> list[dict]:
    if not campaign_ids:
        return []

    tasks = [
        _fetch_metrics_batch(client, campaign_ids[i:i + _BATCH_SIZE], start, end, "CAMPAIGN", granularity)
        for i in range(0, len(campaign_ids), _BATCH_SIZE)
    ]
    results = await asyncio.gather(*tasks)
    all_rows = [row for batch in results for row in batch]
    logger.info("Fetched %d campaign metric rows", len(all_rows))
    return all_rows


async def fetch_creative_metrics(
    client: LinkedInClient,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date,
    granularity: str = "DAILY",
) -> list[dict]:
    if not campaign_ids:
        return []

    tasks = [
        _fetch_metrics_batch(client, campaign_ids[i:i + _BATCH_SIZE], start, end, "CREATIVE", granularity)
        for i in range(0, len(campaign_ids), _BATCH_SIZE)
    ]
    results = await asyncio.gather(*tasks)
    all_rows = [row for batch in results for row in batch]
    logger.info("Fetched %d creative metric rows", len(all_rows))
    return all_rows


async def fetch_demographics(
    client: LinkedInClient,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date,
    pivots: list[str] | None = None,
) -> dict[str, list[dict]]:
    if not campaign_ids:
        return {}

    if pivots is None:
        pivots = DEMOGRAPHIC_PIVOTS

    demographics: dict[str, list[dict]] = {}

    async def _fetch_pivot(pivot: str) -> tuple[str, list[dict]]:
        try:
            all_rows: list[dict] = []
            for i in range(0, len(campaign_ids), _BATCH_SIZE):
                batch = campaign_ids[i:i + _BATCH_SIZE]
                rows = await _fetch_metrics_batch(
                    client, batch, start, end, pivot, "ALL",
                )
                all_rows.extend(rows)
            return pivot, all_rows
        except Exception:
            logger.warning("Failed to fetch demographics for pivot %s", pivot)
            return pivot, []

    results = await asyncio.gather(*[_fetch_pivot(p) for p in pivots])
    for pivot, rows in results:
        demographics[pivot] = rows

    logger.info("Fetched demographics for %d pivot(s)", len(demographics))
    return demographics
