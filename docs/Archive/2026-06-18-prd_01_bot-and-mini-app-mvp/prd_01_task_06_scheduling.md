# Task 06 — Scheduling

## Goal
Implement session creation (one-off + weekly recurring), cancellation, and athlete-scoped calendar reads. Covers all `scheduling/` spec scenarios.

## Scope
**In:** `Session` table; RRULE handling; `POST /sessions`, `POST /sessions/:id/cancel`, `GET /sessions?from&to`; occurrence expansion for the next 60 days.
**Out:** attendance/log/results (Task 07), reminders (Task 08).

## Subtasks
1. Migrate `Session` (`id`, `group_id`, `workout_template_id NULLABLE`, `scheduled_at`, `duration_min`, `recurrence_rule NULLABLE`, `status`).
2. Add RRULE parsing/expansion library (RFC 5545); restrict to `FREQ=WEEKLY` for MVP, multi-day `BYDAY` allowed.
3. Implement `POST /sessions` (trainer-only): validate group ownership; reject past `scheduled_at`; persist with `status=scheduled`.
4. Implement `POST /sessions/:id/cancel` (trainer-only): allowed only when `status=scheduled`; transition to `cancelled`.
5. Implement `GET /sessions?from&to`:
   - Trainer: all sessions of trainer-owned groups in window.
   - Athlete: sessions of groups where the athlete's membership is `active`, with RRULE expanded to concrete occurrences in window.
6. Persist materialized occurrences for the next 60 days in a `session_occurrences` view OR generate on read with a cap of 100 returned.

## Deliverables
- Migration(s) for `Session`
- RRULE expander module + tests
- 3 HTTP routes
- Documentation snippet in `docs/decisions/05-recurrence.md` explaining materialization choice

## Definition of Done
- [ ] One-off session creation succeeds with future `scheduled_at`
- [ ] Past `scheduled_at` → `400`
- [ ] Weekly RRULE session: `GET /sessions` over a 30-day window returns ≥ 4 expanded occurrences
- [ ] Cancel transitions only from `scheduled`; already-`completed` cancel → `409`
- [ ] Athlete calendar excludes sessions of groups where they are `removed`

## Tests
Tied to `specs/scheduling/spec.md` scenarios:
- "Trainer schedules a one-off session"
- "Trainer schedules a weekly-recurring session"
- "Past-dated session is rejected"
- "Cancel scheduled session" (verify notification cancellation in Task 08 follow-up)
- "Cancel rejected after completion"
- "Athlete calendar view is scoped"

## Dependencies
Tasks 02, 04, 05.
