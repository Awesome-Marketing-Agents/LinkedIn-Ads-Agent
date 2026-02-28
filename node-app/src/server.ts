/**
 * Fastify application entry point.
 *
 * Replaces both Flask (main.py) and FastAPI (callback.py) with a single server.
 */

import Fastify from "fastify";
import cors from "@fastify/cors";
import { authRoutes } from "./routes/auth.js";
import { syncRoutes } from "./routes/sync.js";
import { statusRoutes } from "./routes/status.js";
import { reportRoutes } from "./routes/report.js";
import { logger } from "./logger.js";

const PORT = parseInt(process.env.PORT ?? "5001", 10);

const app = Fastify({
  logger: false, // We use our own pino logger
});

// Register plugins
await app.register(cors, { origin: true });

// Register routes
await app.register(authRoutes);
await app.register(syncRoutes);
await app.register(statusRoutes);
await app.register(reportRoutes);

// Health check
app.get("/api/health", async () => ({ status: "ok", timestamp: Date.now() }));

// Start server
try {
  await app.listen({ port: PORT, host: "0.0.0.0" });
  logger.info(`Server running at http://localhost:${PORT}`);
} catch (err) {
  logger.error(`Failed to start server: ${err}`);
  process.exit(1);
}
