# Module: CLI Entry Point

## Overview

`cli.py` provides a command-line interface for the LinkedIn Ads Action Center. It supports `auth`, `sync`, and `status` commands for developers and automation.

---

## File Path

`cli.py`

---

## Components & Explanation

- **`cmd_auth()`** — Runs OAuth flow or checks existing tokens. If not authenticated, prints the auth URL and prompts for the `code` query parameter.
- **`cmd_sync()`** — Performs full data sync: ad accounts → campaigns → creatives → metrics → demographics → assemble → persist (JSON + SQLite).
- **`cmd_status()`** — Prints token status, DB row counts, and active campaign audit.
- **`COMMANDS`** — Dict mapping command names to handler functions.
- **`main()`** — Parses `sys.argv`, dispatches to the matching command, or prints usage.

---

## Relationships

- Uses `AuthManager`, `LinkedInClient`, fetchers, metrics, snapshot, repository.
- Duplicates `sys.path` setup (in addition to `bootstrap`) for robustness.
- Same sync logic as `main.py` but with different creative fetch pattern (all campaigns at once).

---

## Example Code Snippets

```bash
# Authenticate (interactive)
uv run python cli.py auth

# Sync all data
uv run python cli.py sync

# Show status
uv run python cli.py status
```

```bash
# Expected output for status (authenticated)
# -- Token Status --------------------------------------------------
#   Authenticated  : yes
#   Access token   : 45 days remaining
#   Refresh token  : 60 days remaining
#   Last saved     : 2026-02-22T12:00:00+00:00
#
# -- Database -------------------------------------------------------
#   ad_accounts                    :      1 rows
#   campaigns                      :     12 rows
#   ...
```

```python
# Programmatic usage (e.g., in a script)
import subprocess
result = subprocess.run(["uv", "run", "python", "cli.py", "status"], capture_output=True, text=True)
print(result.stdout)
```

---

## Edge Cases & Tips

- **Auth flow**: CLI auth prints a URL; user must open it, authorize, and paste the `code` from the redirect URL.
- **Sync without auth**: Exits with code 1 and message to run `auth` first.
- **No ad accounts**: Sync completes but reports "No ad accounts found. Nothing to sync."
- **Creative fetch**: Uses `fetch_creatives(client, account_id, campaign_ids)` for all campaigns; more efficient than per-campaign calls.

---

## Architecture / Flow

```
User runs: uv run python cli.py <command>
    │
    └── main()
            ├── auth  → cmd_auth()   → AuthManager flow or status
            ├── sync  → cmd_sync()   → fetch → assemble → persist
            └── status → cmd_status() → token + DB + audit
```

---

## Node.js Equivalent

- `cli.py` is replaced by `node-app/src/cli.ts`, which uses Commander.js for argument parsing.
- The same commands are supported: `auth`, `sync`, `status`.
- Run with: `npx tsx src/cli.ts auth|sync|status`.
- Key improvement: the sync command uses `Promise.all` for parallel metric, creative, and demographic fetching, resulting in roughly 3-4x faster sync times compared to the sequential Python implementation.

---

## Advanced Notes

- Docstring says `python main.py` but the actual entry point is `cli.py`.
- Sync uses a 90-day date range, same as the web dashboard.
- Progress is printed step-by-step (e.g., `[1/6] Fetching ad accounts...`).
