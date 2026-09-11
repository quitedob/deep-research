# Deep Research

Authenticated chat and research with a Vue frontend, FastAPI, PostgreSQL, Redis, and AgentScope. The default model is **`deepseek-flash`**, used for text and vision. The interface uses blue and teal accents in light and dark modes.

## Setup

Use Python 3.12, Node.js 20.19+ or 22.12+, PostgreSQL, and Redis. From a fresh checkout on Windows:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Set `JWT_SECRET_KEY` to a random secret of at least 32 bytes. Configure PostgreSQL (`DATABASE_URL` or `DB_*`), Redis, and `DEEPSEEK_API_KEY`. The application requires PostgreSQL and Redis; it fails startup when persistence or token security is unavailable. Schema mismatches stop startup with a migration error and never trigger table deletion. Existing SHA-256 password hashes upgrade after successful login.

`DEEPSEEK_DEFAULT_MODEL=deepseek-flash` selects the default text/vision model. The exact identifier is passed to the configured `DEEPSEEK_BASE_URL`. Explicit session model choices remain supported. Research web search additionally requires `WEB_SEARCH_API_KEY` or `BIGMODEL_API_KEY`. Optional memory uses DeepSeek for fact extraction and HyDE text, Ollama for embeddings, and local Chroma storage; set `MEMORY_ENABLED=false` when that optional stack is not configured.

```powershell
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. The frontend uses `/api` through the development proxy. Set `VITE_API_BASE_URL` in `frontend/.env` for a different deployment URL and list allowed browser origins in `CORS_ALLOWED_ORIGINS`. Production hosts must serve the SPA fallback for client routes, including `/share/:shareId`.

Run one API worker. A PostgreSQL advisory lock prevents concurrent application workers from losing in-process research task ownership. On restart, unfinished persisted research is reported as interrupted and can be resumed from stored request/checkpoint data. Streams authenticate with bearer headers; the optional WebSocket expects `{"token":"<access token>"}` as its first frame within ten seconds.

Shares are explicit snapshots with random identifiers and expiration; authenticated owners can revoke them with `DELETE /api/share/{id}`. Reports, feedback, uploaded content, and evidence verification persist in PostgreSQL. Editing/regenerating a saved turn creates a new conversation branch while preserving the original. Evidence without a measured score displays “未评估”. Uploads accept UTF-8 text up to 50 MiB and images up to 10 MiB; image analysis uses the configured default VLM.

## Verification

```powershell
.venv/Scripts/python.exe scripts/run_checks.py
.venv/Scripts/ruff.exe check backend tests scripts app.py
cd frontend
npm test
npm run lint:check
npm run build
```

Database integration tests create a unique temporary schema and remove only that schema. They require configured PostgreSQL. For Redis tests, provide an isolated local Redis instance; tests never flush a Redis database:

```powershell
$env:RUN_DATABASE_TESTS = '1'
$env:TEST_REDIS_PORT = '<isolated Redis port>'
.venv/Scripts/python.exe scripts/run_checks.py
```

External model/source checks under `tests/live/` require `RUN_LIVE_TESTS=1` and may consume provider credits. They are skipped by default. Regression tests replace only external provider boundaries and exercise real persistence, token rotation, and quotas when integration services are enabled.

The original audit is in [docs/report.md](docs/report.md); implementation evidence and limitations are tracked in [docs/repair-verification.md](docs/repair-verification.md). Provider manuals in `docs/providers/` are archived reference material, not the current configuration contract. See [docs/architecture.md](docs/architecture.md) for source layout and conventions.
