# mini-app — living spec

## Requirements

### Requirement: Mini-App authenticates via Telegram initData
The Mini-App MUST send `initData` to `POST /auth/telegram` on every cold start and MUST NOT render any role-dependent screen before the auth response returns.

#### Scenario: Cold start handshake
- GIVEN a freshly opened Mini-App with valid `initData`
- WHEN the Mini-App boots
- THEN the first network call is `POST /auth/telegram` with the raw `initData`
- AND no `GET /me` or other data calls occur before that response

### Requirement: Role-appropriate home screen on first paint after auth
The Mini-App MUST route a trainer to a trainer home (groups + schedule) and an athlete to an athlete home (upcoming sessions) immediately after `GET /me` returns.

#### Scenario: Trainer lands on trainer home
- GIVEN `GET /me` returns `{role: "trainer"}`
- WHEN the response is received
- THEN the visible screen has a "Groups" list and a "Schedule" tab

#### Scenario: Athlete lands on athlete home
- GIVEN `GET /me` returns `{role: "athlete"}`
- WHEN the response is received
- THEN the visible screen has an upcoming-sessions list and no group-management controls

### Requirement: Mini-App ships a small, fast initial bundle
The Mini-App MUST serve an initial JavaScript+CSS payload ≤ 250 KB gzipped and MUST reach a first interactive frame in ≤ 2 seconds on a 4 Mbps / 100 ms RTT connection.

#### Scenario: Bundle size budget
- GIVEN the production build
- WHEN the CI build step inspects the emitted assets
- THEN the sum of gzipped initial JavaScript and CSS is ≤ 250 KB
- AND CI fails if the budget is exceeded

### Requirement: Athlete can log a workout result in three taps
The Mini-App MUST let an athlete on the session detail screen log a single set with no more than three taps: open exercise → enter actual values → confirm.

#### Scenario: Three-tap log path
- GIVEN an athlete on the session detail of session `S` with exercise `E1` (`unit=kg`)
- WHEN the athlete taps `E1`, fills `reps=8, weight=80`, and taps "Save"
- THEN the Mini-App calls `POST /sessions/S/log` once and the new set appears in the list without a full page reload

### Requirement: Schedule view shows expanded recurring occurrences
The Mini-App MUST render expanded occurrences of recurring sessions over a 14-day rolling window for the current user.

#### Scenario: Weekly session appears twice in 14 days
- GIVEN a weekly-recurring session created last Monday
- WHEN an active member opens the schedule tab today
- THEN the next two occurrences are visible with distinct dates and times

### Requirement: Trainer can review athlete history from Mini-App
The Mini-App MUST let a trainer open an athlete's history showing past sessions, attendance, and per-exercise logs.

#### Scenario: Trainer opens an athlete's history
- GIVEN trainer `T` and athlete `A` with at least one completed session in `T`'s group
- WHEN `T` opens `A`'s profile in the Mini-App
- THEN the screen lists past sessions in reverse-chronological order, each expandable to show logs
