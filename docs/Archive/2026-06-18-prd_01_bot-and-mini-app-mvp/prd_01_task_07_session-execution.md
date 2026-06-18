# Task 07 — Session execution

## Goal
Implement attendance (athlete + trainer sides), workout result logging, and auto-completion. Covers all `sessions/` spec scenarios.

## Scope
**In:** `Attendance` and `WorkoutLog` tables; `POST /sessions/:id/attendance` (athlete), `POST /sessions/:id/attendance/:athlete_id` (trainer), `GET /sessions/:id/log`, `POST /sessions/:id/log`, auto-completion sweep.
**Out:** reminder messages and broadcast (Task 08), Mini-App UI (Task 10).

## Subtasks
1. Migrate `Attendance` (`session_id`, `athlete_id`, `status`), composite PK.
2. Migrate `WorkoutLog` (`session_id`, `athlete_id`, `exercise_id`, `set_index`, `actual_reps?`, `actual_weight?`, `actual_seconds?`, `note?`).
3. Initialize `pending` attendance rows for every active member when a session is created (chain into Task 06 handler).
4. Implement athlete `POST /sessions/:id/attendance`: allow `confirmed | declined` only while `scheduled_at + duration_min > now`; otherwise `409`.
5. Implement trainer `POST /sessions/:id/attendance/:athlete_id`: allow `present | absent` only when `scheduled_at <= now`; otherwise `409`.
6. Implement `POST /sessions/:id/log`: enforce contiguous `set_index` starting at 1 per `(session, athlete, exercise)`; reject when athlete attendance not in `{confirmed, present}`.
7. Implement `GET /sessions/:id/log`: trainer sees all rows; athlete sees only their own.
8. Implement auto-completion sweep (hourly cron): set `Session.status = completed` when all active members are `present|absent` OR when `scheduled_at + duration_min + 24h < now`.

## Deliverables
- 2 migrations
- 4 HTTP routes + integration with Task 06 session-creation handler
- Auto-completion sweep job

## Definition of Done
- [ ] Athlete `pending → confirmed`, `pending → declined` work; post-session change → `409`
- [ ] Trainer `confirmed → present` after start; pre-start → `409`
- [ ] Out-of-order set index rejected; error message includes the next expected index
- [ ] Athlete `GET /sessions/:id/log` returns only own rows
- [ ] Auto-completion via both triggers verified in tests

## Tests
Tied to `specs/sessions/spec.md` scenarios:
- "Athlete confirms via Mini-App"
- "Attendance change blocked after session ends"
- "Trainer marks present"
- "Marking present before start is rejected"
- "Athlete logs first set"
- "Out-of-order set index is rejected"
- "All attendance set ⇒ completed"
- "Grace window elapses ⇒ completed"
- "Trainer reads session log"
- "Athlete sees only own log rows"

## Dependencies
Tasks 02, 04, 06.
