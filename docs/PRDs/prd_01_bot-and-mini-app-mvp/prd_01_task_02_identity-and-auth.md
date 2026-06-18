# Task 02 — Identity & auth

## Goal
Implement user identity and the Telegram-initData auth layer that every subsequent HTTP route will reuse. Covers all `identity/` spec scenarios.

## Scope
**In:** DB schema for `User`, `/start` (no-payload variant), `POST /auth/telegram`, `GET /me`, initData HMAC validation library, 24h freshness check, role-based middleware skeleton.
**Out:** invite redemption flow (Task 03), groups, sessions.

## Subtasks
1. Define and migrate `User` table per the data model in PRD-01.
2. Implement `/start` (no payload): create trainer on first user; reply with onboarding text + Mini-App button.
3. Implement initData HMAC validator (HMAC-SHA256, sorted params, bot-token-derived key); covered by unit tests against Telegram-provided sample payload.
4. Implement `POST /auth/telegram`: validate initData, ensure `auth_date` within 24h, upsert `User` if absent (but only for already-known Telegram ids; otherwise `401`), return session token.
5. Implement `GET /me`.
6. Auth middleware applied to all `/api/*` routes; default-deny if not present.

## Deliverables
- Backend migration adding `User` table
- Bot handler for `/start` (no payload)
- HMAC validator module + tests
- `POST /auth/telegram` and `GET /me` endpoints
- Auth middleware mounted globally

## Definition of Done
- [ ] First `/start` ever received creates a `trainer`
- [ ] Second user without invite receives "Ask your trainer for an invite link" and no `User` row is created
- [ ] Tampered initData → `401`; stale initData (auth_date > 24h) → `401`
- [ ] `GET /me` returns `{id, telegram_id, name, role}` for an authed caller
- [ ] Middleware refuses unauthed `/api/*` requests with `401`

## Tests
Tied to spec scenarios in `specs/identity/spec.md`:
- "First message creates a trainer"
- "Second user without invite is treated as athlete-pending"
- "Tampered initData is rejected"
- "Stale initData is rejected"
- "Trainer onboarding stopwatch" — integration test using a Telegram simulator, asserting elapsed wall-clock ≤ 120 s from `/start` to `GET /me 200`.

## Dependencies
Task 01.
