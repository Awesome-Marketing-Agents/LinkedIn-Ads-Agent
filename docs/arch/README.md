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
