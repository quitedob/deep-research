# Frontend bug-fix browser verification

Executed 2026-09-11 using Chrome DevTools MCP in isolated context `frontend-bugfix-tests`, against the Vite dev server at `http://127.0.0.1:3017`.

The browser executed the real Vue application. `browser-fixture.js` replaced only HTTP calls to `/api/*` and `/health` with disposable responses; it did not contact a provider or database. These checks establish frontend behavior and outgoing contracts, not production backend integration.

| Check | Observed result |
| --- | --- |
| Login and onboarding | Login with no `welcome_completed` flag reached `/home`; account/password inputs had accessible names. |
| Chinese IME | A composing Enter preserved `输入法测试` and issued zero requests. A normal Enter submitted the message. |
| Chat streaming | One-byte network chunks, including split Chinese UTF-8 and CRLF, rendered `中文回复，传输完整。`; the request carried a bearer header. |
| Non-streaming deep think | `/api/chat/chat` rendered `message.content`; no `[object Object]` appeared. |
| Research streaming | Authenticated `GET /api/research/stream/fixture-research` rendered the completion report and retained evidence metadata. |
| Evidence | Expanding the report issued authenticated evidence requests; missing scores read `未评估`. |
| Reporting | Submitting the report dialog issued authenticated `POST /api/moderation/report` and displayed a real toast. |
| Dialog keyboard | Share dialog was named, modal, and initially focused. Shift+Tab wrapped to its last control; Escape closed it and returned focus to the trigger. |
| Logout | One server logout request; both storage locations had access and refresh credentials removed; Pinia message/history lengths were zero; route was `/login`. |
| Public share | Anonymous `/share/fixture-share` loaded without an authorization header. Model HTML and fenced script text produced zero image/script elements and no executed payload. |
| Runtime diagnostics | No Vue/runtime console warnings or errors after the exercised flows. |

The automated `npm test` suite separately covers refresh concurrency, rejected refresh after logout, multipart boundaries, malformed/terminal SSE, registration validation, notification registration and confirmation settlement, and late history responses after logout. `npm run lint:check` and `npm run build` passed. The production build retains a warning for the existing large syntax-highlighting bundle.

To repeat the browser fixture checks, start the Vite dev server on a disposable port, open an isolated browser context, inject `browser-fixture.js` before navigating or submitting the login form, and use only the fixture account. Never inject the fixture into a production session.

## Blue and teal theme verification

After the user's request to remove purple, all retained application CSS/Vue/SVG color values were audited, including translucent gradients/shadows and syntax highlighting. The former imported syntax theme was replaced by `src/assets/code-theme.css`. A hue scan found zero remaining non-neutral values between 225 and 340 degrees. Browser computed-style scans on the landing page, dark chat with highlighted Python, and light settings found zero matching colors.

Screenshots captured at a 1440px-wide browser viewport:

- `blue-teal-landing-final.png`: blue/teal landing gradient and legible pale cyan hero text.
- `blue-teal-chat-dark.png`: slate navigation, blue chat accents and cyan/teal highlighted code.
- `blue-teal-settings-light.png`: light slate settings, blue controls and visible keyboard focus.

The chat/code screenshot uses disposable fixture messages; no real model output or user data was captured.


## Final review follow-ups (2026-09-12)

Using the real Vue app in isolated context `repair-final-checks`, with disposable HTTP responses:

- Settings → Data Management → Clear History opened a named modal confirmation. Tab reached Confirm, continued to Cancel, and wrapped to Close. Escape closed the confirmation and returned focus to Clear History; no DELETE was sent. The underlying settings dialog remained available.
- Regenerating the second answer sent `before_message_id: 3` to the branch route, then streamed the original second question against `fixture-branch`. The preceding pair was loaded with fresh IDs 101/102 before streaming. All edit/regenerate buttons were disabled during a held partial reply.
- Stopping the partial reply retained fresh prefix IDs 101/102. Saved prefix actions became available while unsaved draft actions remained disabled. Editing the first prefix message then sent `before_message_id: 101` (not the original ID 1), and rendered the final edited response with persisted IDs after reload.
- The separate actual FastAPI/PostgreSQL/Redis journey proves branch ownership, fresh IDs, preserved original transcripts, and exclusion of original later turns from provider context. Browser HTTP was a fixture; no real model was called.

During source editing, Vite full reloads discarded the injected fixture and produced expected failed requests to the unavailable local backend. Fixtures were re-injected before the final action checks above; those development reload errors are not treated as backend-integration evidence.
