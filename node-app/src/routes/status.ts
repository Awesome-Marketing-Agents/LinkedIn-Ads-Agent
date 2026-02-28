/**
 * Status API routes.
 */

import type { FastifyInstance } from "fastify";
import { AuthManager } from "../auth/manager.js";
import { tableCounts, activeCampaignAudit } from "../storage/repository.js";

export async function statusRoutes(fastify: FastifyInstance): Promise<void> {
  fastify.get("/api/status", async () => {
    const auth = new AuthManager();
    const tokenStatus = auth.tokenStatus();

    let dbCounts: Record<string, number> = {};
    let audit: Array<{ name: string; issues: string[] }> = [];

    try {
      dbCounts = tableCounts();
    } catch (e) {
      dbCounts = { error: -1 };
    }

    try {
      audit = activeCampaignAudit();
    } catch {
      audit = [];
    }

    return {
      token: tokenStatus,
      database: dbCounts,
      active_campaign_audit: audit,
    };
  });
}
