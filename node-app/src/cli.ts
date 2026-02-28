#!/usr/bin/env node

/**
 * LinkedIn Ads Action Center -- CLI entry point.
 *
 * Usage:
 *   npx tsx src/cli.ts auth       Run the OAuth flow (or verify existing tokens)
 *   npx tsx src/cli.ts sync       Pull all data from LinkedIn and persist locally
 *   npx tsx src/cli.ts status     Print token and database health summary
 */

import { Command } from "commander";
import { AuthManager } from "./auth/manager.js";
import { LinkedInClient } from "./ingestion/client.js";
import {
  fetchAdAccounts,
  fetchCampaigns,
  fetchCreatives,
} from "./ingestion/fetchers.js";
import {
  fetchCampaignMetrics,
  fetchCreativeMetrics,
  fetchDemographics,
} from "./ingestion/metrics.js";
import {
  assembleSnapshot,
  saveSnapshotJson,
} from "./storage/snapshot.js";
import {
  persistSnapshot,
  tableCounts,
  activeCampaignAudit,
} from "./storage/repository.js";
import { DATABASE_FILE } from "./config.js";
import fs from "node:fs";

const program = new Command();
program.name("linkedin-ads").description("LinkedIn Ads Action Center CLI");

// ── auth ──────────────────────────────────────────────────────────────────

program.command("auth").description("Authenticate or verify existing tokens").action(async () => {
  const auth = new AuthManager();

  if (auth.isAuthenticated()) {
    console.log("Already authenticated.");
    await auth.checkTokenHealth();
  } else {
    console.log("No valid token found.");
    console.log("Visit this URL to authorise the application:\n");
    console.log(`  ${auth.getAuthorizationUrl()}\n`);
    console.log("After authorising, paste the ?code= value from the redirect URL:");

    // Read from stdin
    const readline = await import("node:readline");
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const code = await new Promise<string>((resolve) => {
      rl.question("  code> ", (answer) => {
        rl.close();
        resolve(answer.trim());
      });
    });

    await auth.exchangeCodeForToken(code);
    console.log("Authentication complete.");
  }

  const status = auth.tokenStatus();
  console.log(
    `\nAccess token  : ${status.access_token_expired ? "EXPIRED" : "valid"} (${status.access_token_days_remaining} days remaining)`,
  );
  if (status.refresh_token_days_remaining != null) {
    console.log(`Refresh token : ${status.refresh_token_days_remaining} days remaining`);
  }
});

// ── sync ──────────────────────────────────────────────────────────────────

program.command("sync").description("Pull all data from LinkedIn and persist locally").action(async () => {
  const auth = new AuthManager();
  if (!auth.isAuthenticated()) {
    console.log("Not authenticated. Run 'auth' command first.");
    process.exit(1);
  }

  const client = new LinkedInClient(auth);
  const today = new Date();
  const dateStart = new Date(today);
  dateStart.setDate(dateStart.getDate() - 90);

  const fmtDate = (d: Date) => d.toISOString().split("T")[0];
  const days = Math.floor((today.getTime() - dateStart.getTime()) / 86400000);
  console.log(`Date range: ${fmtDate(dateStart)} -> ${fmtDate(today)} (${days} days)\n`);

  // 1. Fetch entities
  console.log("[1/6] Fetching ad accounts...");
  const accounts = await fetchAdAccounts(client);
  console.log(`      Found ${accounts.length} account(s).\n`);

  if (accounts.length === 0) {
    console.log("No ad accounts found. Nothing to sync.");
    return;
  }

  const account = accounts[0];
  const accountId = account.id as number;

  console.log("[2/6] Fetching campaigns...");
  const campaigns = await fetchCampaigns(client, accountId);
  for (const c of campaigns) c._account_id = accountId;
  console.log(`      Found ${campaigns.length} campaign(s).\n`);

  const campaignIds = campaigns.map((c) => c.id as number);

  console.log("[3/6] Fetching creatives...");
  const creatives = await fetchCreatives(client, accountId, campaignIds);
  console.log(`      Found ${creatives.length} creative(s).\n`);

  // 2. Fetch metrics -- KEY PERFORMANCE WIN: parallel fetching
  console.log("[4-6/6] Fetching metrics + demographics in parallel...");
  const start = performance.now();

  const [campMetrics, creatMetrics, demographics] = await Promise.all([
    fetchCampaignMetrics(client, campaignIds, dateStart, today),
    fetchCreativeMetrics(client, campaignIds, dateStart, today),
    fetchDemographics(client, campaignIds, dateStart, today),
  ]);

  const elapsed = ((performance.now() - start) / 1000).toFixed(2);
  console.log(`      ${campMetrics.length} campaign metric rows.`);
  console.log(`      ${creatMetrics.length} creative metric rows.`);
  const totalDemo = Object.values(demographics).reduce((s, v) => s + v.length, 0);
  console.log(`      ${totalDemo} demographic segments across ${Object.keys(demographics).length} pivots.`);
  console.log(`      Completed in ${elapsed}s (parallel).\n`);

  // 3. Assemble and persist
  console.log("Assembling snapshot...");
  const snapshot = assembleSnapshot(
    [account],
    campaigns,
    creatives,
    campMetrics,
    creatMetrics,
    demographics,
    dateStart,
    today,
  );

  const jsonPath = saveSnapshotJson(snapshot);
  const sizeKb = (fs.statSync(jsonPath).size / 1024).toFixed(1);
  console.log(`  JSON   -> ${jsonPath} (${sizeKb} KB)`);

  persistSnapshot(snapshot as any);
  const dbSize = (fs.statSync(DATABASE_FILE).size / 1024).toFixed(1);
  console.log(`  SQLite -> ${DATABASE_FILE} (${dbSize} KB)`);

  console.log("\nSync complete.");
});

// ── status ────────────────────────────────────────────────────────────────

program.command("status").description("Print token health and database row counts").action(async () => {
  const auth = new AuthManager();
  const status = auth.tokenStatus();

  console.log("-- Token Status " + "-".repeat(48));
  if (status.authenticated) {
    console.log("  Authenticated  : yes");
    console.log(`  Access token   : ${status.access_token_days_remaining} days remaining`);
    if (status.refresh_token_days_remaining != null) {
      console.log(`  Refresh token  : ${status.refresh_token_days_remaining} days remaining`);
    }
    console.log(`  Last saved     : ${status.saved_at ?? "N/A"}`);
  } else {
    console.log(`  Authenticated  : no (${(status as any).reason ?? "token expired or missing"})`);
  }

  console.log();
  console.log("-- Database " + "-".repeat(52));
  try {
    const counts = tableCounts();
    for (const [table, count] of Object.entries(counts)) {
      console.log(`  ${table.padEnd(30)}: ${String(count).padStart(6)} rows`);
    }
  } catch (e) {
    console.log(`  Could not read database: ${e}`);
  }

  console.log();
  console.log("-- Active Campaign Audit " + "-".repeat(40));
  try {
    const audit = activeCampaignAudit();
    if (audit.length === 0) {
      console.log("  No active campaigns found.");
    }
    for (const entry of audit) {
      if (entry.issues.length > 0) {
        console.log(`  ${entry.name}: ${entry.issues.join(", ")}`);
      } else {
        console.log(`  ${entry.name}: no issues detected`);
      }
    }
  } catch {
    console.log("  (no data yet)");
  }
});

program.parse();
