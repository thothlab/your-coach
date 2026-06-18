# scheduling — delta for PRD-01

## ADDED Requirements

### Requirement: Trainer schedules one-off and recurring sessions
The system MUST let a trainer create a session for a group at a future time, optionally with a workout template attached, and optionally with a weekly recurrence rule.

#### Scenario: Trainer schedules a one-off session
- GIVEN a trainer-owned group `G` and template `W`
- WHEN the trainer submits `POST /sessions` with `{group_id: G, workout_template_id: W, scheduled_at: <future ISO datetime>, duration_min: 60}`
- THEN the API returns `201` with `Session.status = scheduled` and no `recurrence_rule`

#### Scenario: Trainer schedules a weekly-recurring session
- GIVEN a trainer-owned group `G`
- WHEN the trainer submits `POST /sessions` with `{group_id: G, scheduled_at: <Mon 19:00>, duration_min: 60, recurrence_rule: "FREQ=WEEKLY;BYDAY=MO"}`
- THEN the system stores one master `Session` row with the rule
- AND `GET /sessions?from=<today>&to=<+30d>` returns at least 4 expanded occurrences derived from the rule

#### Scenario: Past-dated session is rejected
- GIVEN any trainer
- WHEN the trainer submits `POST /sessions` with `scheduled_at` in the past
- THEN the API responds `400 Bad Request` and no row is created

### Requirement: Trainer can cancel a scheduled session
The system MUST let the owning trainer cancel a session that is still `scheduled` and MUST cancel pending notifications for that session.

#### Scenario: Cancel scheduled session
- GIVEN a `scheduled` session with two pending reminder notifications
- WHEN the trainer submits `POST /sessions/:id/cancel`
- THEN the session transitions to `cancelled`
- AND every related `Notification` row transitions `scheduled → cancelled`
- AND no reminder is delivered to athletes after this point

#### Scenario: Cancel rejected after completion
- GIVEN a session with `status = completed`
- WHEN the trainer submits `POST /sessions/:id/cancel`
- THEN the API responds `409 Conflict`

### Requirement: Athlete sees only sessions of groups they belong to
The system MUST scope `GET /sessions?from&to` for an athlete to sessions of groups where the athlete's membership is `active`.

#### Scenario: Athlete calendar view is scoped
- GIVEN athlete `A` is `active` in group `G1` and `removed` from `G2`
- WHEN `A` calls `GET /sessions?from=<today>&to=<+14d>`
- THEN every returned session has `group_id = G1`
