Code Review — D:\python\deep-research

  Mode: Full repository audit · Report-only (no files were modified) · Scope: entire repo, excluding .venv/,
  vue/node_modules/, vue/dist/, __pycache__/, .git/, .idea/, .vscode/
…fol
──Verdict

  The stack mostly startsdand the happy path partially works —login, chat sessions, streaming chat, and the research
  SSE flow reach real endpoints. But:

  - 1 committed live API key, a full authorization bypass, and unsalted password hashing.
  - 3 modules are structurally unimportable (tts/, security/quota.py, sqlmodel/) —meaning no rate limiting exists at
  all.
  - Data is silently discarded: every DAO write swallows exceptions and returns None, and the entire citation pipeline
  never persists.
  - The user's structural complaint is confirmed: ~174 KB of vendor .txt manuals plus clean.cmd sit loose at the root,
  and several folder names are genuinely misleading.

  ---
  HIGH — Confirmed defects

  H1. Live API key committed to git

  test/testsearch.py:13 —a real BigModel/Zhipu key is hardcoded, and the file is tracked (git ls-files
  test/testsearch.py →tracked; introduced in b19e63b).

  API_KEY = "f4799605...e1abfdf.rpo5rizn684an7Ym"

  Impact: anyone with repo read access has a billable credential. Rotate this key first —it is in git history and
  cannot be un-leaked by deleting the line. Then move the value to .env and reference os.getenv("BIGMODEL_API_KEY").

  H2. Authentication bypass —"optional auth" silently degrades to anonymous

  src/middleware/auth.py:86-92:

  async def get_optional_user(authorization: Optional[str] = Header(None)):
      if not authorization:
          return None
      try:
          return await get_current_user(authorization)
      except HTTPException:
          return None          # invalid/expired/garbage token →anonymous

  Every ownership check is wrapped in if current_user: (src/api/deep_research.py:106-110, 241-245, 281), so omitting the
  header or sending a deliberately broken token skips the check entirely:

  - GET /api/research/export/{session_id} (:231) →returns the full report, findings, citations and memory of any
  session ID.
  - GET /api/research/stream/{session_id} (:396) →no ownership check at all; the handler accepts current_user and never
  reads it.
  - GET /api/research/status/{session_id}, /sessions, /search →same pattern.

  The frontend cannot authenticate the SSE call anyway (EventSource cannot set headers), so the stream endpoint is only
  ever used unauthenticated. Verify: curl http://localhost:8000/api/research/export/<any-session-id> with no
  Authorization header.

  Also note GET /api/research/sessions?user_id=<victim> (:195) and ?user_id= on /search (:302-310) let a query parameter
  override the authenticated identity.

  H3. Cross-user content disclosure in search

  src/services/agentscope_research_service.py:797-812:

  if session_ids:
      ...per-session loop...
  else:
      results = await self.research_dao.search_research_content(query=query, limit=limit)

  user_id=None (anonymous) →global search over all users' content. Worse: a user with user_id but no sessions yields
  session_ids == [], which is falsy →also global. Compounded by H14 below (the per-session filter only binds to one of
  three UNION branches).

  H4. Unsalted SHA-256 password hashing

  src/services/user_service.py:30,35:

  return hashlib.sha256(password.encode()).hexdigest()
  ...
  return UserService.hash_password(password) == password_hash   # not constant-time

  No salt, no KDF. Two users with the same password get identical hashes; the DB yields instantly crackable digests. Use
  passlib/bcrypt or argon2.

  H5. Token refresh is dead —users are forcibly logged out

  src/api/user.py:123:

  async def refresh_token(refresh_token: str):     # no Body() →FastAPI treats this as a QUERY param

  FastAPI places a bare str in a POST into query_params, so every client sending a JSON body gets 422. Both callers send
  JSON (vue/src/api/index.js:72-75, vue/src/utils/apiClient.js:50-56). Compounding: userAPI.refreshToken has zero
  callers anywhere in the frontend, so a 401 permanently strands the user. Fix: refresh_token: str = Body(...,
  embed=True), then actually wire it into the 401 path.

  H6. Every DAO write can fail silently; citations never persist

  src/dao/base.py:127-131,160-164 catch Exception and return None/[] (while execute_query:92-96 re-raises). All inserts
  routed through fetch_one therefore return None on any DB error, and callers read None as a business outcome.

  This is why a real data-loss bug is invisible: db_schema.py:130 declares authors TEXT[], research_dao.py:222 writes
  json.dumps(authors) (a str), research_models.py:65 declares Column(JSON), and get_session_citations reads it back with
  json.loads (:255) —three mutually inconsistent representations. asyncpg rejects a str for TEXT[] →DataError →
  swallowed →add_citation returns None →research_agent.py:518-529 logs success anyway. Citations are dropped on every
  research run.

  H7. Frontend renders [object Object] for non-streaming chat

  vue/src/views/Home.vue:117-127:

  const response = await chatAPI.chat({ ..., stream: false });
  chatStore.updateMessageContent({ ..., contentChunk: response.content || response.message });

  Backend ChatResponse is {session_id, message: ChatMessage, usage} (src/schemas/chat.py:60-64) where message is an
  object. response.content is undefined, so the object is concatenated into the bubble. Correct field:
  response.message.content. Reachable from the deep-think (clock) toggle.

  H8. Four frontend features are guaranteed to 404

  ┌───────────────┬───────────────────────────────────────────────┬────────────────────┐
  │    Feature    │                   Evidence                    │  Backend reality   │
  ├───────────────┼───────────────────────────────────────────────┼────────────────────┤
  │ 举报 (report) │ MessageItem.vue:564 →/api/moderation/report  │ no such router     │
  ├───────────────┼───────────────────────────────────────────────┼────────────────────┤
  │ 分享 (share)  │ MessageItem.vue:658 →/api/share/conversation │ no such router     │
  ├───────────────┼───────────────────────────────────────────────┼────────────────────┤
  │ 上传文件      │ FileUpload.vue:137 →/rag/upload-document     │ no RAG router      │
  ├───────────────┼───────────────────────────────────────────────┼────────────────────┤
  │ 证据链        │ EvidenceChain.vue:137 →/evidence/...         │ no evidence router │
  └───────────────┴───────────────────────────────────────────────┴────────────────────┘

  All four also send localStorage.getItem('token') (MessageItem.vue:568,662) while the app only ever writes auth_token
  (api/index.js:19) →Bearer null even before the 404.

  H9. Users can get permanently stuck on the welcome page

  vue/src/router/index.js:127-130 forces every authenticated route to /welcome while welcome_completed !== 'true'. That
  flag is written only by views/Welcome.vue:16,33, driven solely by the FeatureTour completion event. Dismiss the tour
  with ×and every alternative CTA loops back to /welcome. Verify: set auth_token, delete welcome_completed, navigate to
  /home.

  Related: vue/src/router/index.js:15 declares path: '/' with redirect: '/home', which Vue Router resolves before global
  guards —so the guard's to.path === '/' branch (:80-98) is dead code, and the /landing marketing page is unreachable
  by normal navigation.

  H10. Three layers are structurally unimportable

  Run any one of these and the module raises at import:

  ┌───────────────────────────────────────────┬─────────────────────────────────────┬───────────────────────────────┐
  │                  Module                   │            Broken import            │            Reality            │
  ├───────────────────────────────────────────┼─────────────────────────────────────┼───────────────────────────────┤
  │ src/core/tts/tts_manager.py:13,           │ from ...config.logging.logging      │ src/config/logging/ does not  │
  │ tts_service.py:13                         │ import get_logger                   │ exist                         │
  ├───────────────────────────────────────────┼─────────────────────────────────────┼───────────────────────────────┤
  │ src/core/security/quota.py:13             │ from src.core.cache import cache    │ src/core/cache/ does not      │
  │                                           │                                     │ exist                         │
  ├───────────────────────────────────────────┼─────────────────────────────────────┼───────────────────────────────┤
  │ src/sqlmodel/research_models.py:14        │ from src.sqlmodel.models import     │ src/sqlmodel/models.py does   │
  │                                           │ Base                                │ not exist                     │
  └───────────────────────────────────────────┴─────────────────────────────────────┴───────────────────────────────┘

  quota.py has zero importers, which means the application has no rate limiting or quota enforcement of any kind (grep
  for rate_limit|throttle|quota across src/api/ and src/middleware/ →nothing). tts/ and sqlmodel/ are also unreferenced
  dead code. TTS additionally implements only EDGE; the other 6 TTSEngine members raise NotImplementedError.

  H11. API key written in plaintext to the repository root

  src/core/agentscope/config.py:216-217,232-233,254-260 builds LLMConfig(api_key=os.getenv("DEEPSEEK_API_KEY")) and then
  json.dump(self._config.dict(), ...) to agentscope_config.json in the CWD on first get_config(). The DeepSeek key
  lands unencrypted at the repo root where it can be committed. Verify: delete the file, run the app, grep -o
  '"api_key": "[^"]*"' agentscope_config.json.

  H12. jwt.JWTError does not exist in PyJWT 2.x →500 instead of 401

  src/core/security/jwt_manager.py:141:

  except jwt.JWTError as e:

  PyJWT 2.8.0 exports only PyJWTError; evaluating the except clause raises AttributeError, which escapes decode_token.
  Any invalid token (bad signature, malformed) returns HTTP 500 instead of a clean 401.

  H13. Frontend hardcodes localhost:8000 on the two primary flows

  vue/src/views/Home.vue:181,268,444 use absolute http://localhost:8000/... for chat streaming and the research
  EventSource, bypassing the Vite proxy. There are three different base-URL strategies and two different env var names
  (VITE_API_BASE_URL in api/index.js:4 vs VITE_APP_API_BASE_URL in services/api.js:4), and vue/src/utils/apiClient.js:6
  is hardcoded with no env var at all. On any non-localhost deployment, login works but chat and research break.

  H14. Per-session search filter binds to only one UNION branch

  src/dao/research_dao.py:366-372 appends AND session_id = $2 to the end of a three-way UNION ALL string, so it applies
  only to the final research_memory branch. research_findings and research_citations are returned from all sessions even
  when scoped. The same query uses json_array_elements_text(cast(authors as json)) on a text[] column →cannot cast
  type text[] to json, swallowed →always [].

  Also search_research_content passes raw user input into to_tsquery('english', $1): input like AI: the future or a & b
  raises a Postgres syntax error, which is swallowed and returned as 200 {"results": []} —a server failure disguised as
  "no matches".

  H15. SSE stream never terminates for several reachable statuses

  src/api/deep_research.py:411-529 breaks only on completed / failed / not_found. But get_research_status can also
  return "error" (agentscope_research_service.py:354-359), "interrupted" (written by interrupt_research:388-392), or
  "active" for a session not in memory after a restart. EventSource auto-reconnects, so the browser polls forever with
  no completion and no error surfaced. There is also a race: get_research_status does del
  self.active_researchers[session_id] on first observation of task.done(), so a second concurrent poll raises KeyError  →
  caught →"error" →stuck. The while True also has no overall deadline.

  H16. Destructive DDL driven by a heuristic schema check

  src/dao/db_init.py:128-131 →:233 runs DROP TABLE IF EXISTS {table_name} CASCADE on any reported mismatch. But
  _validate_table_schema:197-210 iterates only expected columns, and _types_match:214-229 falls through to a
  case-insensitive string compare for any type not in type_mappings. A false-positive match →silent total data loss for
  users, chat_sessions, user_facts on startup.

  ---
  MEDIUM —Confirmed defects

  #: M1
  Finding: Chat usage rejects real provider payloads →500 after a successful chat. usage: Optional[Dict[str,int]] can't

    hold OpenAI-style prompt_tokens_details objects; FastAPI turns the response-validation failure into a 500 after the
    message was persisted and the user was billed.
  Evidence: src/schemas/chat.py:64, src/services/chat_service.py:267
  ────────────────────────────────────────
  #: M2
  Finding: Failed web search returned as a successful assistant message (HTTP 200) —f"联网搜索失败: …"is persisted as
    the model's reply.
  Evidence: src/services/chat_service.py:401-417
  ────────────────────────────────────────
  #: M3
  Finding: web_search_service references an undefined constant —self.GENERATE_QUERIES_PROMPT (only
    SYNTHESIZE_ANSWER_PROMPT exists). AttributeError swallowed →always degrades to [user_question].
  Evidence: src/services/web_search_service.py:72 vs :21
  ────────────────────────────────────────
  #: M4
  Finding: Multi-image analysis always fails —self.analyze.analyze_image(...) where the attribute is self.analyzer. The

    AttributeError is caught and reported per-image as "分析异常".
  Evidence: src/core/agentscope/tools/image_analysis_tool.py:168 vs :75
  ────────────────────────────────────────
  #: M5
  Finding: Blocking, timeout-less network I/O inside async def —urllib.request.urlopen(url) with no timeout= in
    arxiv_tool.py:367, and a synchronous ZhipuAI(...).chat.completions.create() in web_search_tool.py:70-89. Both freeze

    the entire event loop.
  Evidence: as cited
  ────────────────────────────────────────
  #: M6
  Finding: CORS allow_origins=["*"] + allow_credentials=True —Starlette reflects any origin when a Cookie header is
    present, granting credentialed access to every origin. Masked on relative /api calls by the Vite proxy; live on the
    absolute-URL paths from H13.
  Evidence: app.py:107-113
  ────────────────────────────────────────
  #: M7
  Finding: Global exception handler leaks internals —"detail": str(exc) exposes DSNs, provider responses and file
  paths.
  Evidence: app.py:159-179
  ────────────────────────────────────────
  #: M8
  Finding: ChatService caches a web-search client keyed on nothing —the first call (possibly with an empty key) poisons

    the module-level singleton for the process lifetime.
  Evidence: src/services/web_search_service.py:45-49,233; api/chat.py:23
  ────────────────────────────────────────
  #: M9
  Finding: Refresh tokens accepted as access tokens —if token_type not in ["access", "refresh"] means a 7-day refresh
    token is a valid API credential. (algorithms is pinned, so alg=none is not exploitable.)
  Evidence: src/core/security/jwt_manager.py:160-163
  ────────────────────────────────────────
  #: M10
  Finding: JWT_SECRET_KEY fails open —os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32)) with no startup assertion.

    Currently safe only because of import ordering; any other entry point silently gets a random per-process key,
    invalidating all tokens across restarts with no error.
  Evidence: src/core/security/jwt_manager.py:20
  ────────────────────────────────────────
  #: M11
  Finding: "Memory mode" is a lie —app.py:64 advertises it, but there is no in-memory store: base.py:82-84 returns
  None.
    PUT /api/users/me, PUT /api/users/preferences, and all chat writes return {"success": true} while persisting
  nothing.
     chat_dao.create_session returns None →/api/chat/sessions 500s.
  Evidence: src/dao/base.py:82-84, src/services/user_service.py:212-219
  ────────────────────────────────────────
  #: M12
  Finding: Env-var / provider-name drift makes config inert. llm_config.py:50 reads OLLAMA_DEFAULT_MODEL but .env
  defines
    OLLAMA_MODEL; :69 reads DEEPSEEK_DEFAULT_MODEL but .env has DEEPSEEK_MODEL; :138 tells the operator to set
    ZHIPU_API_KEY while :87 reads BIGMODEL_API_KEY. Three-way divergence between .env, .env.example, and actual
  os.getenv
     calls.
  Evidence: as cited
  ────────────────────────────────────────
  #: M13
  Finding: src/config/memory_config.py has zero importers —the entire MEMORY_* env surface is dead; Mem0MemoryManager
    hardcodes cache_ttl=3600 and expire=300 instead.
  Evidence: memory_manager.py:60,205
  ────────────────────────────────────────
  #: M14
  Finding: Unsynchronized, unbounded in-memory state. active_researchers, session_cache, report_cache
    (agentscope_research_service.py:48-51) and active_sessions (research_memory.py:283) grow forever and are mutated
  from
     concurrent handlers with no lock. cleanup_inactive_sessions misses the two caches. Under multiple uvicorn workers,
  a
     session created in worker A is invisible to worker B →research context silently resets.
  Evidence: as cited
  ────────────────────────────────────────
  #: M15
  Finding: hash() used as a cache key —salted per process by PYTHONHASHSEED, so the query cache never hits across
    restarts/workers; _invalidate_user_cache also never deletes the memory:query: entries it claims to.
  Evidence: src/core/memory/memory_manager.py:175,321-330
  ────────────────────────────────────────
  #: M16
  Finding: Mixed timezone bases in one DB —research_dao.py:53,102,144,227,298 use naive local datetime.now() while
    chat_dao.py/user_dao.py/memory_dao.py use datetime.utcnow(). Cross-table recency ordering is broken by the host's
  UTC
     offset.
  Evidence: as cited
  ────────────────────────────────────────
  #: M17
  Finding: Test accounts seeded into every deployment —demo_user_001..003, test_user with is_active=True,
    is_verified=True, inserted unconditionally at startup.
  Evidence: src/dao/db_init.py:139,246-276
  ────────────────────────────────────────
  #: M18
  Finding: interrupt_research does not cancel the task —the background task is never cancel()ed and
    research_with_completion unconditionally writes "completed", overwriting the user's interrupt.
  Evidence: agentscope_research_service.py:361-406
  ────────────────────────────────────────
  #: M19
  Finding: chat_stream has no error or terminal frame —a mid-stream provider failure ends the body normally and the
    client treats it as a complete answer; api/chat.py:211-218's try/except around StreamingResponse is dead code (the
    generator runs lazily), so an unsupported provider returns 200 with an empty body.
  Evidence: as cited
  ────────────────────────────────────────
  #: M20
  Finding: Chat sessions created by the research flow are unusable —created with llm_provider="agentscope" but
    ChatService._get_llm_instance only knows deepseek/zhipu/ollama →ValueError →500 on every send.
  Evidence: agentscope_research_service.py:696-701, chat_service.py:85-96
  ────────────────────────────────────────
  #: M21
  Finding: Blocking I/O + no retry in providers —a fresh aiohttp.ClientSession per call (no pooling, new TLS handshake
    each time), and BaseLLM._retry_with_backoff has no callers, so max_retries is decorative.
  Evidence: deepseek_llm.py:82,116; base_llm.py:81-155
  ────────────────────────────────────────
  #: M22
  Finding: arXiv query double-prefixing —'search_query': f'all:{query}' applied to helpers that already embed a field
    (cat:, au:, id:) →all:cat:cs.AI returns wrong/empty results. Also the PDF-link branch (:292) is dead because :420
    stores {'arxiv': {...}} while the PDF lives at paper['pdf_url'].
  Evidence: arxiv_tool.py:357,94,136,176,292,420
  ────────────────────────────────────────
  #: M23
  Finding: All LLM failures are mislabelled as content-policy violations —the if "contentFilter" ... branch returns,
    making the fallback-report block below it unreachable. Any exception returns "内容可能包含敏感信息".
  Evidence: research_agent.py:808-832
  ────────────────────────────────────────
  #: M24
  Finding: research_agent.py:101 uses DashScopeChatFormatter() while the configured providers are DeepSeek/Ollama.
    Formatters are provider-specific in AgentScope 1.x.
  Evidence: LIKELY
  ────────────────────────────────────────
  #: M25
  Finding: preferences dict passed to a jsonb param without json.dumps —asyncpg expects str; the codebase's own
    convention (chat_dao.py:196) contradicts this call →PUT /api/users/preferences 500s.
  Evidence: user_dao.py:217-220
  ────────────────────────────────────────
  #: M26
  Finding: Client validation contradicts the server contract on register —/^[A-Za-z0-9]{1,20}$/ applied to both
  username
     and password rejects valid server-side values (john_doe, Passw0rd!) while accepting a 3-char password that then
    422s.
  Evidence: Register.vue:105-119 vs src/schemas/user.py:14-23
  ────────────────────────────────────────
  #: M27
  Finding: Streaming text is silently lost —Home.vue:466-487 splits each network chunk on \n with no residual buffer,
  so
     a data: frame straddling a TCP boundary fails JSON.parse and is only console.warned.
  Evidence: as cited
  ────────────────────────────────────────
  #: M28
  Finding: Logout does not reset client state —UserProfileMenu.vue:69-88 never calls POST /api/users/logout and never
    resets the Pinia store, so logging in as another user briefly shows the previous user's messages and history.
  Evidence: as cited
  ────────────────────────────────────────
  #: M29
  Finding: The entire frontend notification system is dead —composables/useNotifications.js:45 registerToast is never
    called, ToastNotifications.vue has 0 references, so every notification.error() is a silent no-op and confirm() would

    hang its promise forever. Five components import a non-existent @/stores/notification →unresolvable import.
  Evidence: as cited
  ────────────────────────────────────────
  #: M30
  Finding: IME hazard on the primary input of a Chinese-language product —InputBox.vue:7 @keydown.enter.exact.prevent
    does not check event.isComposing, so pressing Enter to commit a Pinyin candidate sends the half-composed  message.
  Evidence: as cited
  ────────────────────────────────────────
  #: M31
  Finding: Systemic accessibility failure —grep -rn "aria-label|role=|aria-modal" vue/src returns zero matches. Form
    inputs have no associated labels; modals set no role="dialog", trap no focus, and don't close on Escape;
    MessageItem's actions are visibility: hidden with no :focus-within (unreachable by keyboard, invisible on touch);
    emoji are used as the only accessible name for the theme toggle and as color-only status.
  Evidence: as cited
  ────────────────────────────────────────
  #: M32
  Finding: vue/.eslintrc.js uses module.exports under "type": "module" →module is not defined when ESLint loads it,
    breaking both npm run lint and lint:check. Rename to .eslintrc.cjs.
  Evidence: vue/.eslintrc.js:1, vue/package.json:5
  ────────────────────────────────────────
  #: M33
  Finding: Errors surfaced via alert() in 8+ files (Login.vue:121, Register.vue:173, HistoryList.vue:105,118,138,
    DataManagementSettings.vue:50-53, MessageItem.vue:593,599,691, InputBox.vue:370,373,403), including several that
    should throw —e.g. "清除历史" calls the non-existent chatStore.clearAllHistory() (DataManagementSettings.vue:48),
    and the TypeError is swallowed into a misleading "清除失败，请重试".
  Evidence: as cited
  ────────────────────────────────────────
  #: M34
  Finding: WebSocket endpoint is unreachable —async def websocket_research_progress(websocket, session_id: str)
    (:567-568) leaves websocket unannotated, so FastAPI treats it as a required query parameter and every connection
    fails validation before accept() runs. Also has no authentication.
  Evidence: as cited
  ────────────────────────────────────────
  #: M35
  Finding: monitor_research_progress is registered as a BackgroundTask at :82-86 but its body is pass —dead code
    implying progress monitoring exists.
  Evidence: api/deep_research.py:554-563
  ────────────────────────────────────────
  #: M36
  Finding: Per-session hardcoded evidence scores —the SSE evidence chain emits "relevance_score": 0.95,
    "confidence_score": 0.90 for every citation, making fabricated scores indistinguishable from measured ones. Other
    unexplained literals: count=20, top_k=5, limit // len(session_ids) + 1, [:300], [:500], and len(agent_report) > 100.
  Evidence: api/deep_research.py:469-470; agentscope_research_service.py:1087

  ---
  Root cause: three systemic patterns

  Most of the above reduce to three recurring defects, all systemic rather than local:

  1. Swallowed exceptions + None as a business value. base.py returns None/[] on any DB error while execute_query
  re-raises —an inconsistent contract that makes H6, H11-adjacent writes, and M11 invisible. The same anti-pattern
  (except Exception: →log) hides M3, M4, M15.
  2. Two sources of truth that were never reconciled. Schema exists as both raw DDL (db_schema.py) and ORM
  (sqlmodel/research_models.py); state management exists as both store/index.js and stores/*.js; the API base URL exists
  three times with two env var names; notifications exist as both a composable and a missing Pinia store. Every one of
  these diverged into a bug.
  3. get_optional_user used where get_current_user was required. One misplaced convenience dependency produced H2, H3
  and the user_id query-param overrides.

  ---
  Repository structure —your specific complaint is valid

  Root pollution: confirmed

  ls -la at the root shows 12 loose files, of which 6 do not belong there:

  ┌───────────────────────────────┬───────┬────────────────────────────────────────────────────────────────────────┐
  │             Path              │ Size  │                             Classification                             │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ app.py                        │ 5.4   │ Required —uvicorn target "app:app"                                    │
  │                               │ KB    │                                                                        │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ requirements.txt, .gitignore, │ —    │ Required at root                                                       │
  │  .env.example                 │       │                                                                        │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ .env                          │ 1.7   │ Correctly placed and correctly ignored —git check-ignore -v .env →   │
  │                               │ KB    │ .gitignore:62; git ls-files .env →empty (not tracked) ✔              │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ clean.cmd                     │ 68 B  │ Misplaced →scripts/                                                   │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ rule.txt                      │ 677 B │ Misplaced →docs/                                                      │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ z_rule.txt                    │ 7.9   │ Misplaced →docs/providers/                                            │
  │                               │ KB    │                                                                        │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ deepseek-rule.txt             │ 17.7  │ Misplaced →docs/providers/                                            │
  │                               │ KB    │                                                                        │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ ollama-rule.txt               │ 47.4  │ Misplaced →docs/providers/                                            │
  │                               │ KB    │                                                                        │
  ├───────────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────┤
  │ doubao_rule.txt               │ 100   │ Misplaced →docs/providers/                                            │
  │                               │ KB    │                                                                        │
  └───────────────────────────────┴───────┴────────────────────────────────────────────────────────────────────────┘

  ≈174KB of pasted vendor API manuals sit at the repository root, five of twelve root files. Untracked junk at root:
  none (root __pycache__/ is correctly ignored).

  Folder naming: confirmed problems

  ┌───────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────┐
  │       Name        │                                           Verdict                                           │
  ├───────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ src/sqlmodel/     │ Worst name in the repo. Named after a library it doesn't use (it imports sqlalchemy),       │
  │                   │ contains one broken file with no __init__.py, and has zero importers.                       │
  ├───────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ vue/              │ Named after a framework, not a role. Should pair with the backend as frontend/.             │
  ├───────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ test/             │ Non-standard plurality —pytest convention is tests/.                                       │
  ├───────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ src/              │ Ambiguous —"src of what?" when two source trees coexist.                                   │
  ├───────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ src/dao/          │ Unexplained abbreviation vs. concept-named siblings (services/, schemas/, middleware/,      │
  │                   │ config/).                                                                                   │
  ├───────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │                   │ Three inconsistent conventions: rule.txt (no separator, unnamed), z_rule.txt (meaningless   │
  │ Root .txt files   │ one-letter z_ prefix), deepseek-rule.txt/ollama-rule.txt (hyphen), doubao_rule.txt          │
  │                   │ (underscore). z_rule.txt is worst —z is an unexplained abbreviation for Zhipu.             │
  ├───────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ testollama.py,    │ Missing the test_ separator →pytest will not collect them. Also 4 files, 4 different       │
  │ testsearch.py     │ naming logics.                                                                              │
  ├───────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ test/1.png,       │ Non-descriptive numeric names; sequence skips 2.                                            │
  │ test/3.jpg        │                                                                                             │
  └───────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────┘

  Also invisible to git: src/core/database/ and src/core/export/ are empty orphaned directories —not ignored (git
  check-ignore exits 1) but never reported, because git does not track empty directories. A database/ folder sitting
  empty beside the real src/dao/ is a trap for the next reader. Same for src/core/security/crypto/ (0-byte __init__.py,
  no implementation).

  Test hygiene: 0 of 6 files are runnable tests

  No test-runner configuration exists anywhere —no pytest.ini, pyproject.toml, setup.cfg, tox.ini, or conftest.py;
  requirements.txt contains no pytest, pytest-asyncio, ruff, mypy, black, or flake8. All six are ad-hoc manual scripts
  (all guard on if __name__ == "__main__"). test_zhipuai.py exposes tests only as methods of a class →pytest collects
  nothing. The async ones would error without pytest-asyncio.

  Two fixtures are broken for a fresh clone: test/3.jpg is tracked but referenced only in a docstring, while test/1.png
  is required by testollama.py:61 but is silently swallowed by the over-broad .gitignore:40 *.png →the test prints
  "图像文件不存在" and silently no-ops instead of failing.

  Missing standard structure

  No README.md (a repo with 174 KB of provider docs has zero onboarding). No Python project metadata or lint/type config
  of any kind, while the frontend has .eslintrc.js —an asymmetry worth closing. No vue/.env.example, and the root
  .env.example contains no VITE_ entries.

  Recommended target layout

  deep-research/
  ├── README.md                  # MISSING —create
  ├── pyproject.toml             # MISSING —pytest/ruff/mypy config
  ├── requirements.txt / requirements-dev.txt
  ├── .env.example  .gitignore
  ├── backend/                   # was src/ —disambiguates from frontend
  │   ├── main.py                # was app.py
  │   ├── api/ config/ core/ middleware/ schemas/ services/
  │   ├── models/                # was sqlmodel/ —delete the dead ORM, or fix it
  │   └── repositories/          # was dao/ —concept-named like its siblings
  ├── frontend/                  # was vue/ —role-named, pairs with backend/
  ├── tests/                     # was test/ —pytest convention
  │   ├── conftest.py            # NEW —sys.path + shared async client + --live marker
  │   └── fixtures/              # 1.png, 3.jpg tracked, with .gitignore negation
  ├── docs/
  │   ├── architecture.md        # from rule.txt  (api →service →core →dao)
  │   └── providers/             # deepseek-api-reference.md, zhipu-api-reference.md, ...
  └── scripts/                   # clean.cmd
  Rename map: testollama.py →test_ollama_image_analysis.py, testsearch.py →test_mcp_web_search.py, test_llm.py →
  test_llm_providers.py, test_zhipuai.py →test_zhipu_api.py —restoring descriptive separators without shortening
  anything.

  ▎ Rename-impact caveat before you move anything: app.py is the uvicorn target string "app:app" (app.py:195) and is the
  ▎ documented entry point; .env/.env.example are consumed by load_dotenv(); rule.txt is referenced by name in no code
  ▎ but is the only repo-authored convention document. vue/vite.config.js:33-34 also declares a dangling alias @rag →
  ▎ ../src/rag, and src/rag/ does not exist.

  ---
  Documentation review

  ┌────────────────────┬──────────────────┬─────────────────────────────────────────────────────────────────────────┐
  │      Document      │   Reliability    │                                  Basis                                  │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │                    │                  │ Layering (api→service→core→daand the LLM-base-class mandate are      │
  │ rule.txt           │ PARTIALLY        │ honored in code; the "implement vendors per root txt files" mandate and │
  │                    │ RELIABLE         │  the frontend principles are not —no 撤销/undo or 退出/exit affordance │
  │                    │                  │  exists anywhere in vue/src                                             │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ deepseek-rule.txt  │ RELIABLE         │ Base URL, temp 1.0, max_tokens 4096 all match llm_config.py:68-74       │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │                    │ RELIABLE         │                                                                         │
  │ ollama-rule.txt    │ (vendor) /       │ Endpoints and port 11434 match ollama_llm.py                            │
  │                    │ UNVERIFIED       │                                                                         │
  │                    │ (usage)          │                                                                         │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ z_rule.txt         │ PARTIALLY        │ Prescribes zai-sdk/ZhipuAiClient while the code uses zhipuai.ZhipuAI    │
  │                    │ RELIABLE         │ (web_search_tool.py:66) —wrong SDK                                     │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │                    │                  │ No Doubao/Ark implementation exists anywhere; factory.py:25-29          │
  │ doubao_rule.txt    │ CONTRADICTED     │ registers only ollama/deepseek/zhipu, and there are zero ARK_*/VOLC_*   │
  │                    │                  │ reads in src                                                            │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │                    │                  │ Documents keys the code never reads (DATABASE_URL, API_HOST/PORT,       │
  │ .env.example       │ CONTRADICTED     │ JWT_ALGORITHM, JWT_EXPIRATION_MINUTES) and omits many the code requires │
  │                    │                  │  (DB_HOST/PORT/USER/PASSWORD/NAME, all DEEPSEEK_*/OLLAMA_*/ZHIPU_*,     │
  │                    │                  │ ACCESS_TOKEN_EXPIRE_MINUTES, WEB_SEARCH_API_KEY)                        │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │                    │                  │ No version is pinned (all >=). Missing 7 imported packages: sqlalchemy, │
  │ requirements.txt   │ STALE            │  zhipuai, jwt, edge_tts, httpx, mcp, pytest. Declares unused aioredis.  │
  │                    │                  │ agentscope>=0.0.5 is a floor while the code imports private 1.x modules │
  │                    │                  │  —installed is 1.0.6                                                   │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ vue/vite.config.js │ CONTRADICTED     │ Names the project "AgentWork" in 4 places; @rag alias is a dead path    │
  ├────────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ app.py docstrings  │ PARTIALLY        │ Declares 1.0.0 vs git's version 0.1; API_HOST/API_PORT are ignored in   │
  │                    │ RELIABLE         │ favor of hardcoded 0.0.0.0:8000                                         │
  └────────────────────┴──────────────────┴─────────────────────────────────────────────────────────────────────────┘

  Repository documentation rules: none exist. There is no convention for review reports, changelogs, devlogs, indexes,
  templates, frontmatter, filenames, links, or documentation validation. rule.txt:1 is the only repo-authored
  convention, and it is silent on file layout —so the restructuring you asked for has no supporting convention and will
  require you to establish one.

  No README.md, CONTRIBUTING.md, docs/, doc/, or CLAUDE.md exists anywhere (all .md glob hits were inside dependencies).

  ---
  Checks run

  - git ls-files, git check-ignore -v (confirmed .env correctly untracked), git status -uall --ignored=matching
  - ls -la / find recursion over root, src/, test/, vue/; find src/core -type d -empty
  - Route-table comparison: every frontend HTTP call against app.py + src/api/*.py
  - Dependency symbol verification against installed sources (PyJWT 2.8.0 exception names; asyncpg array-encoder
  _is_trivial_container; redis aclose vs close) —read from .venv/Lib/site-packages/
  - Grep-based dead-code and referrer analysis for every file listed above

  Not run (and why): the project's .venv/Scripts/python.exe shim resolves to a missing
  C:\Users\shuaibi\anaconda3\python.exe, so no endpoint was exercised end-to-end and no test could be executed. All
  framework-behavior claims were reproduced on a separate Python 3.11 interpreter with FastAPI 0.115/Starlette 0.46 —
  the project pins FastAPI 0.119/Starlette 0.48, so the CORS finding (M6) is the one worth re-checking on 0.48. No npm
  install, npm run build, or network request was performed.

  ---
  Coverage and residual risk

  Reviewed: app.py; all of src/api/, src/services/, src/dao/, src/config/, src/middleware/, src/schemas/, src/core/
  (llm, agentscope, memory, security, tts), src/sqlmodel/; all of vue/src/ (api, services, stores, composables, router,
  views, components); root docs, requirements.txt, .env*; test/.

  Not reviewed (residual risk):
  - vue/dist/ —whether the committed build output is stale relative to vue/src/ was not determined.
  - src/core/agentscope/tools/__init__.py, src/core/memory/__init__.py, src/core/llm/__init__.py exports were inferred
  from importer greps, not read line-by-line.
  - doubao_rule.txt (100 KB) was reviewed structurally, not line-by-line.
  - No live runtime, so all "will 404" claims come from route-table comparison, not observed HTTP.

  Open questions that change severity:
  1. Is allow_credentials=True intentional (M6), or a copy-paste default? Is any cookie auth planned?
  2. Does your DeepSeek/Zhipu account return prompt_tokens_details? One captured response body settles M1.
  3. Does intent/interrupt actually stop the agent (M18), or is interrupt_research purely advisory?
  4. Which is canonical —.env or .env.example? Neither matches the os.getenv calls, so provisioning from either
  silently misconfigures the DB, JWT, and all three LLM providers.
  5. vuex and pinia are both installed; only Pinia is used. Is Vuex intended, or remove it?
  6. Is src/sqlmodel/research_models.py a staged migration, or dead code? Nothing imports it and it cannot import.

  ---
  Frontend dead code (relevant to your folder cleanup)

  Zero references —safe to delete once confirmed: vue/src/utils/apiClient.js, vue/src/services/ollama.js,
  vue/src/composables/useNotifications.js, vue/src/stores/{research,orchestrator}.js (both target non-existent
  /api/research/plans*, /api/orchestrator/* routes →20+ guaranteed 404s), vue/src/views/ChatManagement.vue (not
  routed), vue/src/assets/1.jpg, and 13 components including all five under vue/src/components/research/ (which
  additionally import a non-existent @/stores/notification). Unused deps: vuex, marked, @fortawesome/fontawesome-free.

  Backend dead/unreferenced: src/core/tts/*, src/core/security/quota.py, src/core/security/sanitizer/security.py (its
  regexes can never fire —html.escape runs before the pattern loop), src/sqlmodel/research_models.py,
  src/config/memory_config.py, src/core/llm/utils.py (RetryHandler/with_retry/TokenLogger —definitions only),
  src/core/{database,export,crypto}/ (empty).

  ---
  Recommended order of action

  1. Rotate the leaked API key (test/testsearch.py:13) —it is in git history.
  2. Fix the auth bypass (H2/H3): make get_optional_user propagate 401 on a present but invalid token, and add ownership
  checks to stream_research_progress.
  3. Fix the refresh contract (H5) and the [object Object] render (H7) —both are one-line fixes unlocking dead flows.
  4. Stop swallowing DB exceptions (base.py) —this is the single change that surfaces H6 and M11.
  5. Replace password hashing (H4) and remove jwt.JWTError (H12).
  6. Then the structural cleanup —with the understanding that the folder renames must land after the entry-point and
  env references are updated.