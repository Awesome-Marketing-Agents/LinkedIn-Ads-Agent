/**
 * Sync API routes with SSE streaming for real-time progress.
 */

import { EventEmitter } from "node:events";
import type { FastifyInstance } from "fastify";
import { AuthManager } from "../auth/manager.js";
import { LinkedInClient } from "../ingestion/client.js";
import {
  fetchAdAccounts,
  fetchCampaigns,
  fetchCreatives,
} from "../ingestion/fetchers.js";
import {
  fetchCampaignMetrics,
  fetchCreativeMetrics,
  fetchDemographics,
} from "../ingestion/metrics.js";
import {
  assembleSnapshot,
  saveSnapshotJson,
} from "../storage/snapshot.js";
import { persistSnapshot } from "../storage/repository.js";
import { logger } from "../logger.js";

interface SyncJob {
  id: string;
  status: "running" | "completed" | "failed";
  emitter: EventEmitter;
  result?: Record<string, unknown>;
  error?: string;
}

const jobs = new Map<string, SyncJob>();

async function runSync(job: SyncJob): Promise<void> {
  const emit = (step: string, detail: string) => {
    job.emitter.emit("progress", { step, detail, timestamp: Date.now() });
  };

  try {
    const auth = new AuthManager();
    if (!auth.isAuthenticated()) {
      throw new Error("Not authenticated. Run auth flow first.");
    }

    const client = new LinkedInClient(auth);
    const today = new Date();
    const dateStart = new Date(today);
    dateStart.setDate(dateStart.getDate() - 90);

    emit("1/6", "Fetching ad accounts...");
    const accounts = await fetchAdAccounts(client);
    emit("1/6", `Found ${accounts.length} account(s).`);

    if (accounts.length === 0) {
      emit("done", "No ad accounts found. Nothing to sync.");
      job.status = "completed";
      return;
    }

    emit("1/6", `Found ${accounts.length} account(s). Syncing all...`);

    let allCampaigns: Record<string, unknown>[] = [];
    let allCreatives: Record<string, unknown>[] = [];
    let allCampaignIds: number[] = [];

    for (const account of accounts) {
      const accountId = account.id as number;

      emit("2/6", `Fetching campaigns for ${account.name ?? accountId}...`);
      const campaigns = await fetchCampaigns(client, accountId);
      for (const c of campaigns) c._account_id = accountId;
      allCampaigns.push(...campaigns);

      const campaignIds = campaigns.map((c) => c.id as number);
      allCampaignIds.push(...campaignIds);

      emit("3/6", `Fetching creatives for ${account.name ?? accountId}...`);
      const creatives = await fetchCreatives(client, accountId, campaignIds);
      allCreatives.push(...creatives);
    }

    emit("2/6", `Found ${allCampaigns.length} campaign(s) across ${accounts.length} account(s).`);
    emit("3/6", `Found ${allCreatives.length} creative(s).`);

    // KEY PERFORMANCE WIN: Fetch metrics + demographics in parallel
    emit("4-6/6", "Fetching metrics and demographics in parallel...");

    const [campMetrics, creatMetrics, demographics] = await Promise.all([
      fetchCampaignMetrics(client, allCampaignIds, dateStart, today),
      fetchCreativeMetrics(client, allCampaignIds, dateStart, today),
      fetchDemographics(client, allCampaignIds, dateStart, today),
    ]);

    emit(
      "4-6/6",
      `${campMetrics.length} campaign metrics, ${creatMetrics.length} creative metrics, ${Object.keys(demographics).length} demo pivots.`,
    );

    emit("assemble", "Assembling snapshot...");
    const snapshot = assembleSnapshot(
      accounts,
      allCampaigns,
      allCreatives,
      campMetrics,
      creatMetrics,
      demographics,
      dateStart,
      today,
    );

    const jsonPath = saveSnapshotJson(snapshot);
    emit("persist", `JSON saved to ${jsonPath}`);

    persistSnapshot(snapshot as any);
    emit("persist", "SQLite updated.");

    job.status = "completed";
    job.result = { jsonPath, accountCount: accounts.length };
    emit("done", "Sync complete!");
  } catch (err) {
    job.status = "failed";
    job.error = err instanceof Error ? err.message : String(err);
    job.emitter.emit("progress", {
      step: "error",
      detail: job.error,
      timestamp: Date.now(),
    });
    logger.error(`Sync failed: ${job.error}`);
  }
}

export async function syncRoutes(fastify: FastifyInstance): Promise<void> {
  // Start a sync job
  fastify.post("/api/sync", async () => {
    const jobId = `sync-${Date.now()}`;
    const job: SyncJob = {
      id: jobId,
      status: "running",
      emitter: new EventEmitter(),
    };
    jobs.set(jobId, job);

    // Run in background (don't await)
    runSync(job);

    return { jobId, status: "running" };
  });

  // SSE stream for sync progress
  fastify.get("/api/sync/:jobId/stream", async (request, reply) => {
    const { jobId } = request.params as { jobId: string };
    const job = jobs.get(jobId);

    if (!job) {
      return reply.status(404).send({ error: "Job not found" });
    }

    reply.raw.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    });

    const onProgress = (data: Record<string, unknown>) => {
      reply.raw.write(`data: ${JSON.stringify(data)}\n\n`);
    };

    job.emitter.on("progress", onProgress);

    // Clean up when client disconnects
    request.raw.on("close", () => {
      job.emitter.off("progress", onProgress);
    });

    // If job already finished, send final status
    if (job.status !== "running") {
      reply.raw.write(
        `data: ${JSON.stringify({ step: "done", detail: job.status })}\n\n`,
      );
      reply.raw.end();
    }
  });

  // Get job status
  fastify.get("/api/sync/:jobId", async (request, reply) => {
    const { jobId } = request.params as { jobId: string };
    const job = jobs.get(jobId);

    if (!job) {
      return reply.status(404).send({ error: "Job not found" });
    }

    return {
      id: job.id,
      status: job.status,
      result: job.result,
      error: job.error,
    };
  });
}
