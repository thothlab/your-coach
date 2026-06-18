# Task 03 — Invites

## Goal
Ship single-use invite-link generation and redemption end-to-end, covering all `invites/` spec scenarios including the personal-group race condition.

## Scope
**In:** `Invite` table; `/invite` command; `/start <token>` handler; `POST /groups/:id/invites`; redemption transaction; personal-group concurrency guard.
**Out:** trainer-side group UI in Mini-App (Task 04 / 09).

## Subtasks
1. Migrate `Invite` table with `token UNIQUE`, `expires_at`, `used_at`, `used_by_user_id`.
2. Implement token generator: URL-safe random ≥ 128 bits, low collision probability.
3. Implement `POST /groups/:id/invites` (trainer-only): create row, return `{token, url, expires_at}`.
4. Implement `/invite` bot flow: list trainer groups via inline keyboard; on selection generate invite and reply with URL.
5. Implement `/start <token>` handler: validate token (unused + not expired), create athlete + membership in a single transaction.
6. Implement personal-group guard: atomic `INSERT … WHERE NOT EXISTS (active member of personal group)`; on conflict, rollback and reply "Personal slot already taken".

## Deliverables
- `Invite` migration
- Token generator module + tests
- `POST /groups/:id/invites` route
- `/invite` bot handler
- `/start <token>` bot handler with transactional redemption

## Definition of Done
- [ ] `/invite` round trip (group select → URL reply) ≤ 30 s in a test
- [ ] Redeeming a fresh token: creates `User(role=athlete)`, `Membership(status=pending)`, sets `Invite.used_at`
- [ ] Re-redeeming same token → "already used" reply, no state change
- [ ] Expired token → "expired" reply, no state change
- [ ] Concurrent redemption test (2 redemptions to same personal group within 1 s): exactly one succeeds, the other gets "Personal slot already taken"

## Tests
Tied to `specs/invites/spec.md` scenarios:
- "Trainer generates invite from bot"
- "Invite generation time budget"
- "Fresh athlete redeems valid invite"
- "Reused token is rejected"
- "Expired token is rejected"
- "Two athletes redeem invites to the same personal group" — concurrent integration test

## Dependencies
Task 02 (auth + User table), Task 04 (Group table) — schedule Task 04 strictly before Task 03's `/invite` handler step, OR stub group creation with a SQL fixture.
