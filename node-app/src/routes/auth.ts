/**
 * Auth API routes.
 */

import type { FastifyInstance } from "fastify";
import { AuthManager } from "../auth/manager.js";
import { env } from "../config.js";
import { logAuthEvent } from "../logger.js";

export async function authRoutes(fastify: FastifyInstance): Promise<void> {
  const auth = new AuthManager();

  fastify.get("/api/auth/status", async () => {
    return auth.tokenStatus();
  });

  fastify.get("/api/auth/url", async () => {
    return { url: auth.getAuthorizationUrl() };
  });

  fastify.get("/api/auth/health", async () => {
    const healthy = await auth.checkTokenHealth();
    return { healthy };
  });

  // OAuth callback for web flow
  fastify.get("/callback", async (request, reply) => {
    const query = request.query as Record<string, string>;

    if (query.state !== env.OAUTH_STATE) {
      return reply.status(400).send({ error: "Invalid state parameter." });
    }

    const code = query.code;
    if (!code) {
      return reply.status(400).send({
        error: query.error ?? "unknown",
        description: query.error_description ?? "No error description",
      });
    }

    logAuthEvent("Authorization code received", code.slice(0, 15) + "...");
    await auth.exchangeCodeForToken(code);
    logAuthEvent("Full authentication flow complete");

    return reply.type("text/html").send(`
      <html>
        <head><title>Authentication Successful</title></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
          <h1 style="color: #0077B5;">Authentication Successful!</h1>
          <p>You can now close this tab and return to the application.</p>
          <script>setTimeout(() => window.close(), 3000);</script>
        </body>
      </html>
    `);
  });
}
