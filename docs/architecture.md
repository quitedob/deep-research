# Architecture and repository conventions

The application follows **API → service → core (when needed) → repository**. APIs validate identity and ownership, services coordinate workflows, core modules implement model/research/memory capabilities, and repositories own SQL. Storage failures propagate; callers must never translate a failed write into success.

| Path | Responsibility |
| --- | --- |
| `backend/main.py` | FastAPI routes, startup validation, required PostgreSQL/Redis, one-worker research lock and cleanup |
| `backend/api/` | Authenticated HTTP/SSE/WebSocket contracts and explicit public share lookup |
| `backend/services/` | Chat/research orchestration, document extraction, shared evidence presentation |
| `backend/core/` | Provider abstraction, AgentScope, persistent memory, tokens/quotas, optional TTS |
| `backend/repositories/` | asyncpg queries and non-destructive schema initialization |
| `backend/models/` | SQLAlchemy model declarations matching persisted identifiers/types |
| `backend/schemas/` | Pydantic request/response contracts |
| `frontend/src/` | Vue/Pinia application, shared authenticated fetch and buffered SSE parser |
| `tests/` | Automated regressions, isolated integration fixtures, opt-in external tests in `live/` |
| `docs/providers/` | Archived vendor reference material; no runtime configuration authority |
| `scripts/` | Check runner and workspace-scoped cache cleanup |

Root `app.py` preserves `app:app` and `python app.py` entry points. New code should import `backend.*`. Runtime configuration lives in environment variables (documented in `.env.example` and `frontend/.env.example`); credentials must never be committed or serialized to generated configuration. The default text and vision model is `deepseek-flash`, passed unchanged to the configured provider endpoint. Every model implementation derives from `BaseLLM`; provider calls share pooled asynchronous HTTP sessions with bounded transient retries and explicit stream completion/error handling.

PostgreSQL is required for users, chats, research, reports, shares, uploads, and feedback. Redis persists token revocation, refresh-token rotation, quotas, and caches. Optional memory uses Chroma plus PostgreSQL ownership checks and versioned Redis query caches. Startup creates missing tables but refuses incompatible layouts; schema repair requires an explicit migration, never heuristic deletion. New timestamps are UTC. Research runs in one API process; a PostgreSQL advisory lock enforces this and persisted requests/checkpoints support restart/resume.

The frontend uses blue, teal, and slate in both themes. It uses shared authentication generation guards and abortable requests so account/conversation changes cannot apply stale work. Confirmations must be keyboard-accessible, cancellable, and bound to the account that opened them. Editing/regenerating a saved turn creates a conversation branch containing only preceding messages; the original remains available in history. Raw HTML from model output is disabled. Unknown evidence scores remain unknown.

Keep provider manuals separate from maintained setup instructions. Document API/configuration changes beside the code, add focused regressions for significant behavior, and record repair evidence in `repair-verification.md`. Preserve `report.md` as the original audit. Use descriptive names, role-based directories, and tracked fixtures; do not reintroduce framework-named parallel source trees or unused API wrappers.
