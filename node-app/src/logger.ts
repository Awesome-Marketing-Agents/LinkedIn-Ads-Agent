import pino from "pino";
import fs from "node:fs";
import path from "node:path";
import { LOGS_DIR } from "./config.js";

const logFile = path.join(LOGS_DIR, "linkedin_action_center.log");

// Create a multi-destination logger: console (pretty) + file (JSON)
const streams = [
  // Console with pretty printing
  {
    level: "info" as const,
    stream: pino.transport({
      target: "pino-pretty",
      options: { colorize: true, translateTime: "HH:MM:ss" },
    }),
  },
  // File with structured JSON
  {
    level: "debug" as const,
    stream: fs.createWriteStream(logFile, { flags: "a" }),
  },
];

export const logger = pino(
  { level: "debug" },
  pino.multistream(streams),
);

export function logApiCall(
  method: string,
  endpoint: string,
  statusCode: number,
  duration: number,
): void {
  const status = statusCode >= 200 && statusCode < 300 ? "SUCCESS" : "FAILED";
  logger.info(
    { method, endpoint, statusCode, duration },
    `[${status}] ${method} ${endpoint} -> ${statusCode} (${duration.toFixed(2)}s)`,
  );
}

export function logSyncProgress(
  step: string,
  count: number,
  total?: number,
): void {
  const progress = total ? `[${count}/${total}]` : `[${count}]`;
  logger.info(`SYNC: ${step} ${progress}`);
}

export function logAuthEvent(event: string, details?: string): void {
  const msg = details ? `AUTH: ${event} - ${details}` : `AUTH: ${event}`;
  logger.info(msg);
}

export function logError(error: Error, context?: string): void {
  const msg = context
    ? `ERROR in ${context}: ${error.name}: ${error.message}`
    : `ERROR: ${error.name}: ${error.message}`;
  logger.error({ err: error }, msg);
}
