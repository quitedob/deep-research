# Report repair plan

Scope: all confirmed defects H1–H16 and M1–M36 in `report.md`, plus the associated configuration, test hygiene, and structure issues. The report is the acceptance checklist; a passing build alone is not completion evidence.

## Implementation

1. Repair authentication, password storage, database error propagation, citation representation, safe schema initialization, and scoped search.
2. Repair research lifecycle, cancellation, streaming, provider I/O, configuration, and persistent memory.
3. Unify frontend authentication and API transport; repair rendering, onboarding, notifications, forms, dialogs, and keyboard input.
4. Implement the existing report/share/upload/evidence UI contracts with PostgreSQL persistence and ownership checks. Shares expose an explicit snapshot through a random expiring identifier. Uploads retain content with limits; evidence is derived from persisted citations and separately records user verification. Unknown scores stay unknown.
5. Add regression tests, repair runnable development commands and documentation, move misplaced reference material, and review the integrated changes independently.

The coordinator owns API integration, startup, new interaction persistence, repository metadata, documentation, and final verification. Separate writers own frontend; existing DAO/auth/security; and research/provider/memory services. No overlapping file writers.

## Verification gates

- Security: unauthenticated and cross-user requests fail, refresh cannot authenticate protected APIs, expired/invalid tokens return 401, password hashes are salted, no secret is serialized.
- Persistence: DB errors are observable, citation arrays/preferences round-trip, all search branches are scoped, startup preserves existing data and fails when required services are unavailable.
- Lifecycle: streams end on every terminal state, interrupted tasks stop, concurrent polls are safe, orphaned work is explicit, resource state is bounded.
- UI/API: real route contracts, split SSE frames, refresh retry, account-state reset, toast confirmation, IME and keyboard interaction, build and lint.
- Integrations: controlled local PostgreSQL fixtures and fake provider boundaries; external paid provider runs are separate evidence.

The user confirmed provider-side revocation/rotation of the previously committed BigModel key on 2026-09-11. The source literal has been removed. Historical copies are no longer active according to that confirmation; Git history is preserved.

## Evidence ledger

Implementation and regression verification are complete. Requirement-by-requirement evidence, independent-review follow-ups, and skipped external checks are recorded in `repair-verification.md`.
