# sessions — delta for PRD-01

## ADDED Requirements

### Requirement: Athlete confirms or declines attendance before a session
The system MUST let an athlete with an `active` membership set their attendance status for an upcoming session to `confirmed` or `declined`.

#### Scenario: Athlete confirms via Mini-App
- GIVEN an upcoming session `S` in group `G`, athlete `A` is `active` in `G`, and `Attendance(S, A).status = pending`
- WHEN `A` submits `POST /sessions/S/attendance` with `{status: "confirmed"}`
- THEN the row transitions `pending → confirmed`

#### Scenario: Athlete confirms via reminder message
- GIVEN a reminder Telegram message with inline buttons "Confirm" / "Decline" sent to athlete `A` for session `S`
- WHEN `A` taps "Confirm"
- THEN `Attendance(S, A).status` becomes `confirmed`
- AND the bot updates the message to reflect the choice

#### Scenario: Attendance change blocked after session ends
- GIVEN a session `S` with `scheduled_at + duration_min` in the past
- WHEN athlete `A` submits `POST /sessions/S/attendance` with `{status: "confirmed"}`
- THEN the API responds `409 Conflict`

### Requirement: Trainer marks present or absent during/after a session
The system MUST let the owning trainer set each athlete's attendance to `present` or `absent` from the session's scheduled start onward.

#### Scenario: Trainer marks present
- GIVEN a session `S` whose `scheduled_at` is now or in the past, with athlete `A` and `Attendance(S, A).status = confirmed`
- WHEN the trainer submits `POST /sessions/S/attendance/A` with `{status: "present"}`
- THEN the row transitions `confirmed → present`

#### Scenario: Marking present before start is rejected
- GIVEN a session `S` with `scheduled_at > now`
- WHEN the trainer submits `POST /sessions/S/attendance/A` with `{status: "present"}`
- THEN the API responds `409 Conflict`

### Requirement: Athlete logs workout results during or after the session
The system MUST let an athlete with `Attendance.status ∈ {confirmed, present}` append `WorkoutLog` rows for any exercise in the session's template, with set indexes that are contiguous starting at 1 per exercise.

#### Scenario: Athlete logs first set
- GIVEN a session `S` whose template includes exercise `E1` (unit `kg`), and athlete `A` is `confirmed`
- WHEN `A` submits `POST /sessions/S/log` with `{exercise_id: E1, set_index: 1, actual_reps: 8, actual_weight: 80}`
- THEN the API returns `201` and the row is persisted

#### Scenario: Out-of-order set index is rejected
- GIVEN no prior log rows for `(S, A, E1)`
- WHEN `A` submits a log row with `set_index = 3`
- THEN the API responds `400 Bad Request` referencing the next expected `set_index`

### Requirement: Session auto-completes after a grace window
The system MUST transition a `scheduled` session to `completed` when either the trainer has set every active member's attendance to `present` or `absent`, or `scheduled_at + duration_min + 24h` is in the past.

#### Scenario: All attendance set ⇒ completed
- GIVEN a session `S` with 3 active members, all marked `present` or `absent`
- WHEN the trainer submits the third `POST /sessions/S/attendance/*`
- THEN `Session.status` transitions `scheduled → completed`

#### Scenario: Grace window elapses ⇒ completed
- GIVEN a session `S` with `scheduled_at + duration_min + 24h` now in the past, still `scheduled`
- WHEN the scheduler's hourly sweep runs
- THEN `Session.status` transitions `scheduled → completed`

### Requirement: Trainer and athlete can read session history
The system MUST let the trainer read attendance and logs for any session of their groups, and let an athlete read attendance and logs for sessions of their groups limited to their own log rows.

#### Scenario: Trainer reads session log
- GIVEN a past session `S` of trainer `T`'s group
- WHEN `T` calls `GET /sessions/S/log`
- THEN the response includes log rows for every athlete

#### Scenario: Athlete sees only own log rows
- GIVEN a past session `S` with logs from athletes `A1` and `A2`
- WHEN `A1` calls `GET /sessions/S/log`
- THEN the response includes only rows where `athlete_id = A1`
