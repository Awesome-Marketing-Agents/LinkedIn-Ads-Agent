"""Async entity fetchers for LinkedIn Ads: accounts, campaigns, creatives."""

from __future__ import annotations

from app.linkedin.client import LinkedInClient
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def fetch_ad_accounts(client: LinkedInClient) -> list[dict]:
    logger.info("Fetching ad accounts")
    accounts = await client.get_all_pages("/adAccounts", "q=search")
    logger.info("Fetched %d ad account(s)", len(accounts))
    return accounts


async def fetch_campaigns(
    client: LinkedInClient,
    account_id: int,
    statuses: list[str] | None = None,
) -> list[dict]:
    if statuses is None:
        statuses = ["ACTIVE", "PAUSED", "DRAFT"]

    status_list = ",".join(statuses)
    params = f"q=search&search=(status:(values:List({status_list})))"
    campaigns = await client.get_all_pages(
        f"/adAccounts/{account_id}/adCampaigns", params,
    )
    logger.info("Fetched %d campaign(s) for account %d", len(campaigns), account_id)
    return campaigns


async def fetch_creatives(
    client: LinkedInClient,
    account_id: int,
    campaign_ids: list[int] | None = None,
) -> list[dict]:
    params = "q=criteria&sortOrder=ASCENDING"

    if campaign_ids:
        urns = ",".join(
            f"urn%3Ali%3AsponsoredCampaign%3A{cid}" for cid in campaign_ids
        )
        params += f"&campaigns=List({urns})"

    creatives = await client.get_all_pages(
        f"/adAccounts/{account_id}/creatives", params,
    )
    logger.info("Fetched %d creative(s) for account %d", len(creatives), account_id)
    return creatives


async def resolve_content_references(
    client: LinkedInClient,
    creatives: list[dict],
) -> dict[str, str]:
    """Build human-readable names for content reference URNs.

    Derives display names from the URN type and ID — no extra API calls needed.
    Returns a mapping of content_reference URN -> display name.
    """
    _TYPE_LABELS = {
        "share": "Sponsored Post",
        "adInMailContent": "InMail",
        "video": "Video Ad",
        "ugcPost": "UGC Post",
        "adCreativeV2": "Creative",
    }

    names: dict[str, str] = {}
    for cr in creatives:
        ref = cr.get("content", {}).get("reference", "")
        if not ref:
            continue
        if ref in names:
            continue

        # Extract type and numeric ID from URN like "urn:li:share:12345"
        parts = ref.split(":")
        if len(parts) >= 4:
            entity_type = parts[2]
            entity_id = parts[3]
            label = _TYPE_LABELS.get(entity_type, entity_type)
            names[ref] = f"{label} #{entity_id[-6:]}"
        else:
            names[ref] = ref

    logger.info("Labeled %d content references", len(names))
    return names
