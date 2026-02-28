# LinkedIn Ads Action Center

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![Node.js](https://img.shields.io/badge/node.js-22_LTS-green.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)
![Tooling](https://img.shields.io/badge/tooling-uv-blueviolet.svg)

A comprehensive toolkit for managing and analysing LinkedIn Ads data. Authenticate with the LinkedIn API, ingest campaign data, and view performance metrics — all from a simple web dashboard or a developer CLI.

> **Two implementations** — the original Python stack and a Node.js/TypeScript migration live side-by-side. See sections below for each.

---

## ✨ Key Features

- **OAuth 2.0 Authentication** — securely connect to the LinkedIn API with automatic token refresh.
- **Data Ingestion** — fetch ad accounts, campaigns, creatives, and performance metrics.
- **Local Storage** — persist data in SQLite for offline analysis and historical tracking.
- **Dual Interfaces**
    - **Web Dashboard** (`main.py` / Node.js Fastify server) — click-driven UI for non‑technical users.
    - **CLI** (`cli.py` / `src/cli.ts`) — scriptable commands for developers and CI/CD.
- **Modular Architecture** — clean separation of auth, ingestion, storage, and config.

---

## 🛠️ Tech Stack — Python (Original)

| Layer | Technology |
|---|---|
| Language | Python 3.13+ |
| Package / project manager | [uv](https://docs.astral.sh/uv/) |
| Web framework (OAuth callback) | FastAPI + Uvicorn |
| Web dashboard | Flask |
| Database | SQLite |
| HTTP client | `requests` |

## 🛠️ Tech Stack — Node.js (Migration)

| Layer | Technology |
|---|---|
| Runtime | Node.js 22 LTS |
| Language | TypeScript 5.x |
| Backend | Fastify (port 5002) |
| ORM | Drizzle + better-sqlite3 |
| Frontend | React 19 + Vite + TypeScript (port 3000 dev) |
| HTTP client | Native `fetch` |
| CLI | Commander.js |
| Testing | Vitest |
| Logger | Pino |

### 🚀 Key Improvements in the Node.js Version

- **Parallel API fetching** with `Promise.all` + `p-limit(3)` (~3–4× faster sync).
- **SSE streaming** for real-time sync progress in the browser.
- **Single Fastify server** replaces both Flask and FastAPI.
- **React SPA** with component architecture, TypeScript, and hot reload.
- **Design tokens** extracted to proper CSS files.

---

## 📂 Project Structure

```
.
├── src/                          # Python source
│   └── linkedin_action_center/
│       ├── auth/                 # OAuth flow & token management
│       ├── ingestion/            # API client, fetchers, metrics
│       ├── storage/              # SQLite schema, repository, snapshots
│       └── core/                 # Config & constants
├── node-app/                     # Node.js / TypeScript migration
│   ├── src/
│   │   ├── cli.ts                # CLI entry point (Commander.js)
│   │   └── ...                   # Fastify server, routes, services
│   ├── frontend/                 # React 19 SPA (Vite)
│   │   ├── src/
│   │   └── ...
│   ├── package.json
│   └── .env.example
├── docs/                         # Architecture & sprint docs
├── main.py                       # Web dashboard entry point (Flask)
├── cli.py                        # CLI entry point (Python)
├── bootstrap.py                  # sys.path helper (used by cli.py / main.py)
├── pyproject.toml                # Project metadata & dependencies (managed by uv)
└── .env                          # Environment variables (not committed)
```

---

## 🚀 Getting Started — Python (Original)

### 1. Install `uv`

`uv` is an extremely fast Python package and project manager (written in Rust). It replaces `pip`, `venv`, and `pip-tools` in a single binary.

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify the installation:
```bash
uv --version
```

### 2. Clone & install dependencies

```bash
git clone <repository-url>
cd linkedin-ads-action-center-v1
```

`uv` reads the `pyproject.toml` and creates a virtual environment automatically:

```bash
uv sync
```

That's it — all dependencies listed in `pyproject.toml` are now installed.

> **Adding a new package later?**
> ```bash
> uv add <package-name>
> ```
> This updates `pyproject.toml` *and* the lock file in one step.

### 3. Configure environment variables

Create a `.env` file in the project root (it is git-ignored):

```
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:5000/callback
OAUTH_STATE=some_random_string
```

You can obtain these values from the [LinkedIn Developer Portal](https://www.linkedin.com/developers/).

---

## 🚀 Getting Started — Node.js (Migration)

### 1. Install dependencies

```bash
cd node-app
npm install
```

### 2. Configure environment variables

```bash
cp .env.example .env  # fill in LinkedIn credentials
```

### 3. Start the backend

```bash
cd node-app
npm run dev            # starts Fastify on port 5002
```

### 4. Start the frontend (in another terminal)

```bash
cd node-app/frontend
npm install
npm run dev            # starts Vite dev server on port 3000
```

### 5. Run tests

```bash
cd node-app
npx vitest
```

---

## 🏃‍♀️ Usage — Python (Original)

### Web Dashboard (recommended for everyone)

Start the server:
```bash
uv run python main.py
```

Open **http://127.0.0.1:5000** in your browser. From the dashboard you can:

- **Authenticate** — redirects you to LinkedIn to authorise the app, then handles the callback automatically.
- **Sync Data** — pulls ad accounts, campaigns, creatives, and metrics into the local database.
- **Check Status** — shows token health and database statistics.

### CLI (for developers)

```bash
# Authenticate (interactive)
uv run python cli.py auth

# Sync all data
uv run python cli.py sync

# Show token & DB health
uv run python cli.py status
```

---

## 🏃‍♀️ Usage — Node.js (Migration)

### Web Dashboard

With both the Fastify backend (port 5002) and Vite dev server (port 3000) running, open **http://localhost:3000** in your browser.

The React SPA provides the same workflow — authenticate, sync data, and check status — with real-time SSE streaming for sync progress.

### CLI (for developers)

```bash
# Authenticate (interactive)
cd node-app && npx tsx src/cli.ts auth

# Sync all data
cd node-app && npx tsx src/cli.ts sync

# Show token & DB health
cd node-app && npx tsx src/cli.ts status
```

---

## 🤝 Contributing

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
