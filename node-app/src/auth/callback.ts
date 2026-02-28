/**
 * OAuth callback handler as a Fastify route plugin.
 *
 * Replaces the FastAPI callback server from the Python version.
 * Handles the redirect from LinkedIn after user authorization.
 */

import type { FastifyInstance } from "fastify";
import { env } from "../config.js";
import { AuthManager } from "./manager.js";
import { logAuthEvent } from "../logger.js";

// Store the auth code globally for CLI flow
let authCodeReceived: string | null = null;

export function getAuthCode(): string | null {
  return authCodeReceived;
}

export function resetAuthCode(): void {
  authCodeReceived = null;
}

export async function callbackRoutes(fastify: FastifyInstance): Promise<void> {
  fastify.get("/callback", async (request, reply) => {
    const query = request.query as Record<string, string>;

    // Verify the state parameter to prevent CSRF attacks
    const state = query.state;
    if (state !== env.OAUTH_STATE) {
      return reply.status(400).send({ error: "Invalid state parameter." });
    }

    const code = query.code;
    if (!code) {
      const error = query.error ?? "unknown";
      const errorDescription =
        query.error_description ?? "No error description";
      return reply
        .status(400)
        .type("text/html")
        .send(
          `<h1>Error: ${error}</h1><p>${errorDescription}</p>`,
        );
    }

    logAuthEvent("Authorization code received", code.slice(0, 15) + "...");
    authCodeReceived = code;

    return reply.type("text/html").send(`
      <html>
        <head>
          <title>Authentication Successful</title>
          <style>
            body { font-family: sans-serif; text-align: center; padding-top: 50px; }
            h1 { color: #0077B5; }
            p { color: #333; }
          </style>
        </head>
        <body>
          <h1>Authentication Successful!</h1>
          <p>You can now close this browser tab and return to the application.</p>
        </body>
      </html>
    `);
  });
}
