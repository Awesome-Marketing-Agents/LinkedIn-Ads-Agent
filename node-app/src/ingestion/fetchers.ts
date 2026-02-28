/**
 * Fetchers for LinkedIn Ads entity data: accounts, campaigns, creatives.
 *
 * Each function accepts a LinkedInClient and returns raw dicts straight from
 * the API. No transformation or persistence happens here.
 */

import { LinkedInClient } from "./client.js";

export async function fetchAdAccounts(
  client: LinkedInClient,
): Promise<Record<string, unknown>[]> {
  return client.getAllPages("/adAccounts", "q=search");
}

export async function fetchCampaigns(
  client: LinkedInClient,
  accountId: number,
  statuses: string[] = ["ACTIVE", "PAUSED", "DRAFT"],
): Promise<Record<string, unknown>[]> {
  // LinkedIn REST API uses Restli query syntax
  const statusList = statuses.join(",");
  const params = `q=search&search=(status:(values:List(${statusList})))`;
  return client.getAllPages(`/adAccounts/${accountId}/adCampaigns`, params);
}

export async function fetchCreatives(
  client: LinkedInClient,
  accountId: number,
  campaignIds?: number[],
): Promise<Record<string, unknown>[]> {
  let params = "q=criteria&sortOrder=ASCENDING";

  if (campaignIds && campaignIds.length > 0) {
    const urns = campaignIds
      .map((cid) => `urn%3Ali%3AsponsoredCampaign%3A${cid}`)
      .join(",");
    params += `&campaigns=List(${urns})`;
  }

  return client.getAllPages(`/adAccounts/${accountId}/creatives`, params);
}
