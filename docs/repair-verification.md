# Repair verification

Verification date: 2026-09-12 (Asia/Shanghai). Scope: the original `report.md` findings H1–H16 and M1–M36, related repository/configuration hygiene, the requested default `deepseek-flash` VLM, and removal of purple from the frontend. The original report is preserved.

## Evidence sources

- **Security/persistence:** `tests/test_persistence_security.py` — passwords, tokens, revocation/rotation, quotas, real PostgreSQL arrays/JSON/transactions/scoped search, ORM mappings, non-destructive schema checks.
- **API:** `tests/test_api_boundaries.py` — auth/ownership, research SSE terminal states/deadline, WebSocket handshake, CORS and error handling.
- **Research/providers:** `tests/test_research_providers.py` — real local HTTP pooling/retry/truncation, adapter/image contracts, research cancellation/resume/restart, persisted report/evidence, real Chroma/Redis cache integration, GBK-safe real agent construction/report generation, and optional TTS.
- **Interactions:** `tests/test_interactions.py` — persisted sharing/reporting/feedback/uploads/evidence and conversation-branch ownership.
- **Journey/startup:** `tests/test_user_journey.py`, `tests/test_startup.py` — actual FastAPI routes with real PostgreSQL/Redis, nested provider usage, chat branching/context, authentication lifecycle, required dependencies and one-worker ownership.
- **Frontend:** `frontend/tests/frontend.test.js` — real Pinia modules, auth refresh races, cross-account deletion prevention, stale/stopped history requests, buffered UTF-8 SSE, multipart and input contracts, notifications.
- **Browser:** `frontend/tests/browser-smoke.md` and its screenshots — real Vue with disposable HTTP fixtures. These establish frontend behavior, not live provider/backend browser integration.

## High findings

| Item | Status | Repair and evidence |
| --- | --- | --- |
| H1 | PASS, user-confirmed revocation | Removed source credential/manual script; user confirmed the specific BigModel credential already revoked or rotated on 2026-09-11. Provider console was not independently inspected; history is preserved. |
| H2 | PASS | Optional auth permits absent credentials only; research reads require authentication and ownership. Security + API tests cover anonymous, invalid and cross-account requests. |
| H3 | PASS | Every search requires an owner or explicit owned session scope; users with no sessions cannot trigger global fallback. Real SQL tests cover all branches. |
| H4 | PASS | Salted PBKDF2-HMAC-SHA256, constant-time checking, legacy hash upgrade only after successful login. Security tests. |
| H5 | PASS | Refresh accepts the actual JSON request, rotates persistently, and frontend retries with one concurrent refresh. Security + journey + frontend tests. |
| H6 | PASS | DAO failures propagate; PostgreSQL citation authors use TEXT[]; message/counter and user/preferences writes are atomic. Real SQL rollback/round-trip tests. |
| H7 | PASS | Non-stream chat reads `response.message.content`. Nested usage is accepted. Journey + browser checks. |
| H8 | PASS | Added authenticated report/share/upload/feedback/evidence routes, durable state and public expiring share snapshots. Research reports persist evidence metadata and chat linkage, including after restart. Interaction + research tests; browser contracts. |
| H9 | PASS | Root landing works; onboarding can be dismissed/completed without a redirect trap. Browser login/navigation check. |
| H10 | PASS | Repaired TTS logging imports, Redis quota integration and SQLAlchemy Base/mappings. Only implemented EDGE TTS is advertised. Import, quota, ORM and TTS tests. |
| H11 | PASS | No automatic root config save; explicit config serialization excludes nested secrets. Temporary-file regression test. |
| H12 | PASS | Uses actual PyJWT exceptions and returns 401 for malformed/expired/invalid tokens. Security + API tests. |
| H13 | PASS | Shared configurable frontend HTTP base for normal, stream, multipart and public-share requests; `.env.example` supplied. Frontend/browser checks. |
| H14 | PASS | Owner/session filters apply to all SQL search UNION branches. Real PostgreSQL cross-user tests. |
| H15 | PASS | All unsuccessful terminal states close SSE; stuck streams have a deadline. API tests. |
| H16 | PASS | Startup refuses incompatible schemas, with no heuristic DROP CASCADE. Non-destructive startup test. |

## Medium findings

| Item | Status | Repair and evidence |
| --- | --- | --- |
| M1 | PASS | Usage supports nested provider metadata; actual route journey returns 200 after nested `prompt_tokens_details`. |
| M2 | PASS | Failed web search propagates as failure and does not persist a successful assistant reply. Provider tests. |
| M3 | PASS | Defined and exercised the search-query generation prompt; parses/validates model JSON. Provider test. |
| M4 | PASS | Multi-image analysis uses the configured VLM and preserves all image blocks. Provider test. |
| M5 | PASS | arXiv/search use async HTTP with timeouts; Wikipedia is async too. Source tracing + controlled transport tests; live network checks remain opt-in. |
| M6 | PASS | Explicit CORS origins and no credentialed wildcard. Tested against installed FastAPI/Starlette with untrusted origin/cookie. |
| M7 | PASS | Global/API client errors are generic; exception detail remains server-side. API test injects a secret-like failure. |
| M8 | PASS | Web-search credentials are selected per request rather than cached from the first call. Provider test. |
| M9 | PASS | Protected APIs accept access tokens only. Refresh tokens fail authentication. Security + journey tests. |
| M10 | PASS | Startup validates the actual JWT manager's stable configured secret; missing/weak secrets fail. Security/startup tests. |
| M11 | PASS | PostgreSQL and Redis are required; storage failure never becomes pretend memory-mode success. Startup + DAO + real SQL tests. |
| M12 | PASS | Canonical env examples match runtime; old model/key aliases remain accepted. Default `deepseek-flash` is sent unchanged; unknown unused default-provider example removed. Config/source checks. |
| M13 | PASS | Memory configuration is consumed, including enabled/cache flags and TTLs. Disabled mode creates no clients; enabled mode tested with actual Chroma/SQL/Redis. |
| M14 | PASS | Lifecycle lock, bounded tasks/caches, cleanup, durable reports/checkpoints and database-enforced single-worker ownership. Lifecycle + startup tests. |
| M15 | PASS | Stable SHA-256 query keys include options and a persistent invalidation generation. Real Redis/Chroma test verifies cache hits and mutation invalidation. |
| M16 | PASS for new writes | New timestamps consistently use UTC. SQL/source checks. Historical local-time rows were not guessed or rewritten. |
| M17 | PASS | Demo seeding requires explicit development opt-in; disabled by default. Startup test. |
| M18 | PASS | Interrupt cancels and awaits the actual task before checkpointing; cancellation cannot become completion. Resume restores a real agent checkpoint. Lifecycle tests. |
| M19 | PASS | Provider preparation precedes streaming; errors have explicit frames, incomplete responses are not persisted. OpenAI SSE and Ollama NDJSON require terminal markers; real HTTP truncation tests include model-pull success. |
| M20 | PASS | Research creates usable provider/model chat sessions; legacy `agentscope` sessions map to DeepSeek. Persisted research test + source trace. |
| M21 | PASS | Reused asynchronous sessions, transient retries, no replay after visible stream content, explicit cleanup. Real HTTP connection reuse + retry tests. |
| M22 | PASS | arXiv preserves field-prefixed queries and reads direct PDF URLs. Provider regression. |
| M23 | PASS | Transport/model failures use accurate fallback reporting; content-policy messages are reserved for actual filtering. Provider regression. |
| M24 | PASS | OpenAI/Ollama formatter selection matches providers; tool history and image blocks survive the real formatter/adapter. Provider tests. |
| M25 | PASS | Preferences JSON is encoded/decoded consistently; nested preferences round-trip through actual API and PostgreSQL. |
| M26 | PASS | Frontend registration validation matches server username/password constraints. Frontend tests + register journey. |
| M27 | PASS | Buffered SSE parser handles split UTF-8/CRLF, multi-line frames and final fragments. One-byte Node/browser stream checks. |
| M28 | PASS | Logout calls backend, resets stores, cancels work, invalidates refresh/history operations and destructive confirmations. Delayed A deletion cannot fetch/delete B's sessions. Frontend regressions + browser logout. |
| M29 | PASS | Global toasts are mounted/registered, queued errors become visible, confirmations settle on accept/dismiss. Missing dead notification imports removed. Node/browser tests. |
| M30 | PASS | Composition Enter and Shift+Enter preserve native input; only a completed send key submits. Node + browser IME checks. |
| M31 | PASS for reported controls | Inputs/actions have accessible names, modal focus scopes support Tab/Escape/return focus, actions remain reachable on keyboard/touch. Browser includes nested settings confirmation; no formal WCAG certification claimed. |
| M32 | PASS | ESLint config is `.eslintrc.cjs` for the ESM project; `npm run lint:check` passes. |
| M33 | PASS | Browser alerts replaced with real notifications; clear history uses the actual store action with account guards in both sidebar/settings. Frontend/browser checks. |
| M34 | PASS | WebSocket parameter is typed; first-frame access-token authentication and ownership required before progress disclosure. API test. |
| M35 | PASS | Removed empty background monitor registration; owned research task controls progress/completion. Source trace + lifecycle tests. |
| M36 | PASS | Unmeasured relevance/confidence/quality/relations remain null/unknown; no fabricated fixed scores. Report/evidence tests + browser “未评估”. |

## Additional repairs and layout

- PASS: default text/vision model is `deepseek-flash` in backend/config/frontend; images are sent as multimodal blocks. This records the user-specified provider contract, not an independently verified public model catalog.
- PASS: purple removed from retained CSS/Vue/SVG colors, translucent gradients/shadows, logo and syntax theme. Blue/teal/slate screenshots and computed-style hue scans cover landing, dark chat and light settings.
- PASS: real research-agent construction/report generation no longer fails when Windows stdout uses GBK. The provider boundary is mocked; the agent and adapter are real.
- PASS: edits/regeneration branch an owned persisted conversation prefix before the selected user turn. Original messages stay intact; old later turns are absent from the new model context. Actions are disabled while generating or until message IDs are persisted.
- PASS: renamed source trees to `backend/` and `frontend/`, repositories/models to descriptive directories, retained root entry-point compatibility, replaced broken manual scripts with `tests/` and opt-in `tests/live/`, preserved both image fixtures, removed unreferenced dead wrappers/components and empty placeholders.
- PASS: README, maintained architecture/env examples, pytest/ruff project configuration, pinned direct requirements plus a transitive lock, and safe cache-cleanup scripts. Unused `zhipuai` removed; HTTP search avoids its incompatible PyJWT constraint.

## Commands and limits

Run integration checks with the usable `.repair-venv` Python 3.12 environment, `RUN_DATABASE_TESTS=1`, `TEST_REDIS_PORT` pointing to an isolated Redis, and `MEMORY_ENABLED=false` to prevent module imports using the operator's optional Chroma location. The positive memory test explicitly enables a temporary Chroma store. The original `.venv` launcher pointed to a missing interpreter and was preserved.

Final gates:

| Gate | Status/result |
| --- | --- |
| Backend full regression/integration suite | **PASS — 92 passed, 6 external tests skipped** |
| Actual branch/API journey after fresh-ID assertion | **PASS — 1 passed** |
| Frontend Node suite | **PASS — 12 passed** |
| Frontend ESLint and production build | **PASS** (existing highlighting chunk warning) |
| Ruff runtime-error rules / Python compileall / diff whitespace | **PASS** |
| Source color scan / credential-literal scan | **PASS** — zero purple hue values and zero matching credential literals; this is a pattern scan, not a complete secret-audit guarantee |
| Independent backend and frontend review | Findings fixed by coordinator and checked with focused regressions/browser evidence; see follow-ups below |

 PostgreSQL tests create/drop only unique `repair_test_*` schemas. Redis tests use unique keys and never FLUSHDB. A temporary `deep-research-repair-redis` container supplied 127.0.0.1:1807; the configured Redis endpoint was unavailable during verification and was not rewritten.

- External-provider/source integration: **SKIPPED** (six opt-in tests; no paid model calls).
- Provider-side H1 revocation: **PASS based on user confirmation**, not independently inspected.
- Historical lost citations/local timestamps: **OUT_OF_SCOPE recovery**; fixes prevent new loss, but missing historical data cannot be reconstructed from absent evidence.
- Build: existing large syntax-highlighting chunk warning; successful build, no bundle-size optimization claimed.
- Deployment remains **OUT_OF_SCOPE**. A subsequent user request authorized committing and pushing the reviewed repair, including repository ignore rules.


## Independent-review follow-ups

Separate read-only backend/frontend reviewers audited the integrated tree. Their concrete findings were fixed: missing persisted research evidence/linkage, GBK status-print failures, missing Ollama terminal detection, cross-account clear-all races in both entry points, stale/stopped history loads, keyboard-inaccessible nested confirmations, and edit/regenerate using old context or stale branch IDs. The coordinator added tests and browser checks for each; branch prefix IDs are now loaded from the new session before displaying the branch. Backend reviewer explicitly passed the last real-agent GBK check; frontend reviewer explicitly passed the final fresh-prefix-ID closure. No reviewer changed application files.

Cleanup: the exact temporary Redis container and Vite process on port 3017 were stopped after verification. The disposable browser page was closed. `.repair-venv` remains available for repeatable checks.
