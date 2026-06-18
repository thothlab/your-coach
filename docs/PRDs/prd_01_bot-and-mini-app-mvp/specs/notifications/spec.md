# notifications — delta for PRD-01

## ADDED Requirements

### Requirement: Athletes receive pre-session reminders
The system MUST schedule and deliver two reminder Telegram messages to every active member of a session's group: one at approximately 24 hours before `scheduled_at` and one at approximately 1 hour before.

#### Scenario: Reminders scheduled at session creation
- GIVEN a session `S` created at `T0` with `scheduled_at = T0 + 48h` and one active member `A`
- WHEN the API returns `201` for `POST /sessions`
- THEN two `Notification` rows exist: `(user=A, session=S, kind=reminder, scheduled_at ≈ T0+24h)` and `(user=A, session=S, kind=reminder, scheduled_at ≈ T0+47h)`

#### Scenario: Reminder delivery transitions state
- GIVEN a `Notification` with `scheduled_at ≤ now` and `sent_at IS NULL`
- WHEN the scheduler's hourly sweep runs and Telegram acknowledges delivery
- THEN the row updates `sent_at = now`

#### Scenario: Reminder is idempotent under sweep retries
- GIVEN a `Notification` already `sent`
- WHEN the scheduler runs again
- THEN no duplicate Telegram message is sent for the same `(user_id, session_id, kind, scheduled_at)`

### Requirement: Cancelling a session cancels pending reminders
The system MUST transition every `scheduled` reminder for a cancelled session to `cancelled` and MUST NOT deliver them afterwards.

#### Scenario: Cancel before any reminder fires
- GIVEN a session `S` with two `scheduled` reminders
- WHEN the trainer cancels `S`
- THEN both rows transition `scheduled → cancelled` and no reminder messages are delivered

### Requirement: Reminder messages carry inline Confirm/Decline buttons
The system MUST attach inline-keyboard buttons "Confirm" and "Decline" to every reminder message such that tapping a button updates `Attendance` for that athlete and session.

#### Scenario: Tap Confirm from reminder
- GIVEN a delivered reminder message for `Attendance(S, A).status = pending`
- WHEN athlete `A` taps "Confirm"
- THEN `Attendance(S, A).status` becomes `confirmed`
- AND the message is edited to show "Confirmed ✓"

### Requirement: Trainer can broadcast a text message to a group
The system MUST let a trainer send a one-shot text message that is delivered to every `active` member of a chosen group, up to 5 broadcasts per group per 24-hour window.

#### Scenario: Trainer sends a broadcast
- GIVEN trainer `T` owns group `G` with 3 active members
- WHEN `T` submits `POST /groups/G/broadcast` with `{text: "Bring water"}`
- THEN the API returns `202` with `recipient_count: 3`
- AND each member receives a Telegram message with the text

#### Scenario: Rate limit hit
- GIVEN 5 broadcasts to `G` already delivered in the last 24 hours
- WHEN trainer `T` submits a sixth broadcast
- THEN the API responds `429 Too Many Requests`
