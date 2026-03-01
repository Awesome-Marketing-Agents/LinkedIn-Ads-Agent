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
