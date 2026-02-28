# Architecture Documentation

Beginner-friendly documentation for the **LinkedIn Ads Action Center** codebase. Each document describes a module or file in detail.

---

## Quick Start

- **New to the project?** Start with [00-overview.md](00-overview.md) for the high-level architecture.
- **Working on a specific module?** Use the index below to jump to the right doc.

---

## Document Index

| # | Document | Module / File | Description |
|---|----------|--------------|-------------|
| 00 | [00-overview.md](00-overview.md) | Architecture Overview | System components, data flow, config, dependencies |
| 01 | [01-bootstrap.md](01-bootstrap.md) | `bootstrap.py` | Path helper for `src/` imports |
| 02 | [02-main.md](02-main.md) | `main.py` | Flask web dashboard entry point |
| 03 | [03-cli.md](03-cli.md) | `cli.py` | CLI entry point (`auth`, `sync`, `status`) |
| 04 | [04-auth-manager.md](04-auth-manager.md) | `auth/manager.py` | OAuth token management |
| 05 | [05-auth-callback.md](05-auth-callback.md) | `auth/callback.py` | FastAPI OAuth callback server |
| 06 | [06-ingestion-client.md](06-ingestion-client.md) | `ingestion/client.py` | LinkedIn API HTTP client |
| 07 | [07-ingestion-fetchers.md](07-ingestion-fetchers.md) | `ingestion/fetchers.py` | Entity fetchers (accounts, campaigns, creatives) |
| 08 | [08-ingestion-metrics.md](08-ingestion-metrics.md) | `ingestion/metrics.py` | Analytics & demographics fetchers |
| 09 | [09-storage-database.md](09-storage-database.md) | `storage/database.py` | SQLite schema & connection |
| 10 | [10-storage-repository.md](10-storage-repository.md) | `storage/repository.py` | Data access layer (persist, query) |
| 11 | [11-storage-snapshot.md](11-storage-snapshot.md) | `storage/snapshot.py` | Snapshot assembly & JSON export |
| 12 | [12-core-config.md](12-core-config.md) | `core/config.py` | Environment & paths |
| 13 | [13-core-constants.md](13-core-constants.md) | `core/constants.py` | API URLs & scopes |
| 14 | [14-utils-logger.md](14-utils-logger.md) | `utils/logger.py` | Rich logging |
| 15 | [15-utils-errors.md](15-utils-errors.md) | `utils/errors.py` | Custom exceptions |

---

## Common Commands

```bash
# Install dependencies
uv sync

# Web dashboard
uv run python main.py

# CLI
uv run python cli.py auth
uv run python cli.py sync
uv run python cli.py status

# Tests
uv run pytest tests/ -v
```

---

## Data Flow Summary

```
User (Web or CLI)
    → AuthManager (tokens)
    → LinkedInClient (HTTP)
    → Fetchers + Metrics (API calls)
    → assemble_snapshot (transform)
    → persist_snapshot + save_snapshot_json (storage)
```

---

## Search Tips

- **Authentication**: 04-auth-manager, 05-auth-callback
- **API calls**: 06-ingestion-client, 07-ingestion-fetchers, 08-ingestion-metrics
- **Database**: 09-storage-database, 10-storage-repository
- **Snapshot / JSON**: 11-storage-snapshot
- **Config / env**: 12-core-config, 13-core-constants
- **Logging / errors**: 14-utils-logger, 15-utils-errors

---

## Node.js Migration

The project has been ported to Node.js/TypeScript. The Python architecture documents above still apply conceptually; the Node.js equivalents live under `node-app/`.

### Node.js Document Mapping

| Python Module / File | Node.js Equivalent | Notes |
|----------------------|--------------------|-------|
| `bootstrap.py` | N/A | Not needed; TypeScript resolves paths natively |
| `main.py` (Flask) | `node-app/src/server.ts` (Fastify) | Fastify server + React SPA |
| `cli.py` | `node-app/src/cli.ts` | Commander.js CLI |
| `auth/manager.py` | `node-app/src/auth/manager.ts` | OAuth token management |
| `auth/callback.py` | `node-app/src/auth/callback.ts` | OAuth callback route (Fastify) |
| `ingestion/client.py` | `node-app/src/ingestion/client.ts` | LinkedIn API HTTP client |
| `ingestion/fetchers.py` | `node-app/src/ingestion/fetchers.ts` | Entity fetchers |
| `ingestion/metrics.py` | `node-app/src/ingestion/metrics.ts` | Analytics and demographics fetchers |
| `storage/database.py` | `node-app/src/storage/database.ts` | Drizzle ORM schema and connection |
| `storage/repository.py` | `node-app/src/storage/repository.ts` | Data access layer |
| `storage/snapshot.py` | `node-app/src/storage/snapshot.ts` | Snapshot assembly and JSON export |
| `core/config.py` | `node-app/src/config.ts` | Env vars via dotenv + zod validation |
| `core/constants.py` | `node-app/src/constants.ts` | API URLs and scopes |
| `utils/logger.py` | `node-app/src/utils/logger.ts` | Pino logging |
| `utils/errors.py` | `node-app/src/utils/errors.ts` | Custom error classes |

### Common Node.js Commands

```bash
# Install dependencies
cd node-app && npm install

# Start dev server (Fastify + Vite)
npm run dev

# Run tests
npx vitest

# CLI commands
npx tsx src/cli.ts auth
npx tsx src/cli.ts sync
npx tsx src/cli.ts status
```

### Updated Data Flow (Node.js)

```
User (React SPA or CLI)
    -> AuthManager (tokens)
    -> LinkedInClient (HTTP via fetch)
    -> Promise.all([Fetchers, Metrics]) (parallel API calls)
    -> assembleSnapshot (transform)
    -> persistSnapshot + saveSnapshotJson (Drizzle + JSON)
```
