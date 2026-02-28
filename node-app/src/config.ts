import { config } from "dotenv";
import { z } from "zod";
import path from "node:path";
import fs from "node:fs";

config();

const envSchema = z.object({
  LINKEDIN_CLIENT_ID: z.string().min(1, "LINKEDIN_CLIENT_ID is required"),
  LINKEDIN_CLIENT_SECRET: z.string().min(1, "LINKEDIN_CLIENT_SECRET is required"),
  LINKEDIN_REDIRECT_URI: z
    .string()
    .default("http://localhost:5000/callback"),
  OAUTH_STATE: z.string().default("supersecretstate"),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error("Invalid environment variables:", parsed.error.format());
  process.exit(1);
}

export const env = parsed.data;

// Core Paths
export const BASE_DIR = path.resolve(import.meta.dirname, "..");
export const DATA_DIR = path.join(BASE_DIR, "data");
export const SNAPSHOT_DIR = path.join(DATA_DIR, "snapshots");
export const TOKENS_FILE = path.join(BASE_DIR, "tokens.json");
export const DATABASE_FILE = path.join(DATA_DIR, "linkedin_ads.db");
export const LOGS_DIR = path.join(BASE_DIR, "logs");

// Ensure directories exist
for (const dir of [DATA_DIR, SNAPSHOT_DIR, LOGS_DIR]) {
  fs.mkdirSync(dir, { recursive: true });
}
