# Task 08 — Notifications & broadcasts

## Goal
Schedule and deliver pre-session reminders with Confirm/Decline inline buttons, cancel reminders on session cancellation, and let trainers send rate-limited broadcasts. Covers all `notifications/` spec scenarios.

## Scope
**In:** `Notification` table; reminder scheduling on session create; cancellation propagation; hourly delivery sweep (idempotent); inline-keyboard tap → attendance update; `POST /groups/:id/broadcast` with 5/day/group limit.
**Out:** Mini-App push UX (Task 10).

## Subtasks
1. Migrate `Notification` (`id`, `user_id`, `session_id NULLABLE`, `kind`, `scheduled_at`, `sent_at NULLABLE`, `payload`, UNIQUE `(user_id, session_id, kind, scheduled_at)`).
2. On `POST /sessions` (one-off + each materialized recurring occurrence in 60-day window), insert two `reminder` rows per active member: `scheduled_at - 24h` and `scheduled_at - 1h`.
3. Implement hourly sweep: select `scheduled_at <= now AND sent_at IS NULL`; send via Telegram; set `sent_at` only on success. Skip rows already `sent` or `cancelled`. Cap batch at 500/sweep.
4. Reminder message payload includes an inline keyboard with two callback buttons (`confirm:S` / `decline:S`).
5. Callback handler: validate caller is an `active` member; update `Attendance` accordingly; edit the reminder message to show the chosen state (✓/✗).
6. On `POST /sessions/:id/cancel`, transition all `scheduled` `Notification` rows for that session to `cancelled`.
7. Implement `POST /groups/:id/broadcast`: validate ownership; check 24h rolling window count (≤ 5/group); enqueue `broadcast` notifications for every active member; respond `202` with `recipient_count`.

## Deliverables
- Migration
- Reminder scheduling hook in Task 06's session-create handler
- Hourly sweep job
- Inline-button callback handler
- Cancellation hook in Task 06's cancel handler
- `POST /groups/:id/broadcast` route + rate-limit logic

## Definition of Done
- [ ] Two reminder rows created per active member per session
- [ ] Sweep marks `sent_at` and never delivers the same `(user, session, kind, scheduled_at)` twice
- [ ] Confirm/Decline inline tap updates attendance and edits the message text
- [ ] Cancelling a session cancels all pending reminders for it
- [ ] Broadcast: 6th send in 24h → `429`; under limit → all active members receive the text

## Tests
Tied to `specs/notifications/spec.md` scenarios:
- "Reminders scheduled at session creation"
- "Reminder delivery transitions state"
- "Reminder is idempotent under sweep retries"
- "Cancel before any reminder fires"
- "Tap Confirm from reminder"
- "Trainer sends a broadcast"
- "Rate limit hit"

## Dependencies
Tasks 02, 04, 06, 07.
