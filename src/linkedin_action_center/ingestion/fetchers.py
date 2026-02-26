"""Fetchers for LinkedIn Ads entity data: accounts, campaigns, creatives.

Each function accepts a ``LinkedInClient`` and returns raw dicts straight from
the API.  No transformation or persistence happens here.
"""

from __future__ import annotations

from linkedin_action_center.ingestion.client import LinkedInClient


def fetch_ad_accounts(client: LinkedInClient) -> list[dict]:
    """
    Return all ad accounts the authenticated member has access to.

    Endpoint: GET /rest/adAccounts?q=search
    """
    accounts = client.get_all_pages("/adAccounts", "q=search")
    return accounts


def fetch_campaigns(
    client: LinkedInClient,
    account_id: int,
    statuses: list[str] | None = None,
) -> list[dict]:
    """
    Return all campaigns for *account_id*.

    By default fetches ACTIVE, PAUSED, and DRAFT campaigns (excludes
    ARCHIVED and CANCELED to keep the dataset relevant).

    Endpoint: GET /rest/adAccounts/{id}/adCampaigns?q=search
    """
    if statuses is None:
        statuses = ["ACTIVE", "PAUSED", "DRAFT"]

    # LinkedIn REST API uses Restli query syntax: search=(status:(values:List(A,B,C)))
    status_list = ",".join(statuses)
    params = f"q=search&search=(status:(values:List({status_list})))"
    return client.get_all_pages(f"/adAccounts/{account_id}/adCampaigns", params)


def fetch_creatives(
    client: LinkedInClient,
    account_id: int,
    campaign_ids: list[int] | None = None,
) -> list[dict]:
    """
    Return all creatives for *account_id*, optionally filtered to specific campaigns.

    Endpoint: GET /rest/adAccounts/{id}/creatives?q=criteria
    """
    params = "q=criteria&sortOrder=ASCENDING"

    if campaign_ids:
        urns = ",".join(
            f"urn%3Ali%3AsponsoredCampaign%3A{cid}" for cid in campaign_ids
        )
        params += f"&campaigns=List({urns})"

    creatives = client.get_all_pages(
        f"/adAccounts/{account_id}/creatives", params,
    )
    return creatives
