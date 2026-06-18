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

### Requirement: Trainer can create a group from the Mini-App
The Mini-App MUST expose a "Create group" entry point from the trainer home; the form MUST allow name + type (`group`|`personal`); on submit the new group MUST appear in the trainer's group list without a full page reload.

#### Scenario: Trainer creates a group
- GIVEN a trainer on the Mini-App home
- WHEN the trainer taps "Create group", enters `name="Monday strength"`, selects `type=group`, taps "Save"
- THEN the Mini-App calls `POST /api/groups` once with the matching payload
- AND on success the home group list re-renders with the new entry at the top

#### Scenario: Server validation surfaced inline
- GIVEN the trainer submits the create-group form with `name=""`
- WHEN the API returns `422`
- THEN the Mini-App surfaces the validation message next to the `name` input without navigating away

### Requirement: Trainer can create exercises and workout templates from the Mini-App
The Mini-App MUST let a trainer add exercises (name + unit) and assemble workout templates by picking from the exercise catalog; the form MUST enforce unit-specific target rules client-side and surface server rejections inline.

#### Scenario: Trainer creates an exercise
- GIVEN a trainer on the Mini-App workouts screen
- WHEN the trainer taps "Add exercise", enters `name="Back squat"`, selects `unit=kg`, taps "Save"
- THEN the Mini-App calls `POST /api/exercises` once and the new exercise appears in the catalog list

#### Scenario: Trainer builds a workout template
- GIVEN at least two exercises owned by the trainer
- WHEN the trainer taps "New template", enters `name="Leg day"`, adds two items with valid per-unit targets, taps "Save"
- THEN the Mini-App calls `POST /api/workouts` once with items in the entered order
- AND the new template appears on the templates list immediately

### Requirement: Trainer can schedule sessions from the Mini-App
The Mini-App MUST let a trainer create both one-off and weekly-recurring sessions from a single form; submitting MUST call `POST /api/sessions` exactly once; the new session(s) MUST appear in the schedule view without a full page reload.

#### Scenario: Trainer creates one-off session
- GIVEN a trainer with at least one group and one workout template
- WHEN the trainer fills group, template, start datetime (in future), duration, leaves recurrence empty, taps "Save"
- THEN the Mini-App calls `POST /api/sessions` once with `recurrence_rule = null`
- AND the new session is visible in the trainer home schedule list

#### Scenario: Trainer creates weekly-recurring session
- GIVEN the same setup
- WHEN the trainer toggles "Weekly", picks weekdays (e.g. Mon+Wed), taps "Save"
- THEN the Mini-App submits a `recurrence_rule` of the form `FREQ=WEEKLY;BYDAY=MO,WE`
- AND at least 4 future occurrences appear in the 30-day window of the schedule list

### Requirement: Trainer can compose and send a broadcast from the Mini-App
The Mini-App MUST let a trainer pick a group, write text, and send a broadcast; on success the response `recipient_count` MUST be displayed; on rate limit (`429`) the error MUST be surfaced inline.

#### Scenario: Trainer sends broadcast
- GIVEN a trainer with one group of 3 active members
- WHEN the trainer opens "Broadcast", picks the group, enters "Bring water", taps "Send"
- THEN the Mini-App calls `POST /api/groups/:id/broadcast` once
- AND a success message shows "Sent to 3 members"

#### Scenario: Broadcast hits rate limit
- GIVEN 5 broadcasts already sent to the group in the last 24 hours
- WHEN the trainer submits a sixth
- THEN the Mini-App surfaces "Rate limit reached — try again later" inline and does NOT clear the text field

### Requirement: Mini-App routes use in-app navigation without URL changes
The Mini-App MUST navigate between screens (home, group create, exercises, workouts, session create, broadcast, session detail) without modifying `window.location` (no `?` or `#` parameters mutating during navigation), so Telegram's WebApp back-button behaviour stays consistent.

#### Scenario: Trainer drills into Group Create and back
- GIVEN the trainer is on the home screen
- WHEN the trainer taps "Create group", then the back button (in-app or Telegram's)
- THEN the home screen is restored with the previously seen state
- AND no `location.href` change was emitted between the screens (verified by a `popstate` count of 0 in tests)

