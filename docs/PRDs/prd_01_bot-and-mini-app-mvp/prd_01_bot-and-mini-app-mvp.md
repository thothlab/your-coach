# PRD-01 — Bot + Mini-App MVP

Working title: **your-coach** (placeholder until naming sub-task in Task 01).

## Objective

Ship a Telegram-native MVP that lets a fitness trainer run group and personal training: invite clients, schedule sessions, assign workout templates, collect attendance, log per-athlete results, and remind both sides on time. Both sides (trainer and athlete) operate entirely inside Telegram via a bot + Mini-App.

Success = a real trainer can onboard 3+ athletes, run a full week of sessions, and have a complete log of attendance and results without leaving Telegram.

## Non-objectives

- No payments, subscriptions, or billing
- No public trainer marketplace or discovery
- No native iOS / Android apps; no standalone web app
- No video upload, video review, or live streaming
- No AI workout generation or recommendation
- No multi-trainer / gym / organization mode (single trainer per workspace)
- No internationalization beyond Russian + English copy

## Data model

| Entity | Key fields | Notes |
|---|---|---|
| User | `id`, `telegram_id`, `name`, `role` (`trainer`\|`athlete`), `created_at` | Identity is keyed by Telegram user id; bot writes on `/start`. |
| Group | `id`, `trainer_id`, `name`, `type` (`group`\|`personal`), `created_at` | `personal` group has exactly one active athlete. |
| Membership | `group_id`, `athlete_id`, `status` (`pending`\|`active`\|`removed`), `joined_at` | Composite primary key `(group_id, athlete_id)`. |
| Invite | `id`, `token`, `trainer_id`, `group_id`, `expires_at`, `used_at`, `used_by_user_id` | Single-use; token is URL-safe random ≥ 128 bits. |
| Exercise | `id`, `trainer_id`, `name`, `unit` (`reps`\|`seconds`\|`meters`\|`kg`) | Per-trainer reusable catalog. |
| WorkoutTemplate | `id`, `trainer_id`, `name`, `items` | `items` = ordered `(exercise_id, sets, target_reps, target_weight, target_seconds)`. |
| Session | `id`, `group_id`, `workout_template_id?`, `scheduled_at`, `duration_min`, `recurrence_rule?`, `status` | `recurrence_rule` follows RFC 5545 RRULE; expanded to concrete sessions by scheduler. |
| Attendance | `session_id`, `athlete_id`, `status` (`pending`\|`confirmed`\|`declined`\|`present`\|`absent`) | One row per athlete per session. |
| WorkoutLog | `session_id`, `athlete_id`, `exercise_id`, `set_index`, `actual_reps?`, `actual_weight?`, `actual_seconds?`, `note?` | One row per logged set. |
| Notification | `id`, `user_id`, `session_id?`, `kind` (`reminder`\|`broadcast`), `scheduled_at`, `sent_at`, `payload` | Idempotent by `(user_id, session_id, kind, scheduled_at)`. |

## API list

All non-bot endpoints sit behind Telegram `initData` HMAC validation. Request/response bodies are JSON.

### Bot (Telegram updates)

| Command / event | Actor | Effect |
|---|---|---|
| `/start` (no payload) | unknown user | Register as `trainer` if first message, otherwise greet. |
| `/start <invite_token>` | unknown user | Redeem invite → register as `athlete` and join the invite's group. |
| `/invite` | trainer | Send back a fresh single-use invite link for a chosen group. |
| `/app` | any | Send a button that opens the Mini-App. |
| Reminder push | server → user | Pre-session reminder message with "Confirm" / "Decline" buttons. |
| Broadcast push | server → user | Trainer-authored message routed to all group members. |

### HTTP API (consumed by Mini-App)

| Method | Path | Caller | Purpose |
|---|---|---|---|
| `POST` | `/auth/telegram` | Mini-App | Validate `initData`, return session token. |
| `GET` | `/me` | any | Current user + role. |
| `GET` | `/groups` | trainer | List own groups. |
| `POST` | `/groups` | trainer | Create group. |
| `GET` | `/groups/:id/members` | trainer | List memberships. |
| `POST` | `/groups/:id/invites` | trainer | Generate invite link. |
| `GET` | `/exercises` | trainer | List exercises. |
| `POST` | `/exercises` | trainer | Create exercise. |
| `GET` | `/workouts` | trainer | List workout templates. |
| `POST` | `/workouts` | trainer | Create workout template. |
| `GET` | `/sessions?from&to` | any | Upcoming sessions visible to caller. |
| `POST` | `/sessions` | trainer | Create one-off or recurring session. |
| `POST` | `/sessions/:id/cancel` | trainer | Cancel a scheduled session. |
| `POST` | `/sessions/:id/attendance` | athlete | Set attendance (`confirmed`\|`declined`). |
| `POST` | `/sessions/:id/attendance/:athlete_id` | trainer | Set attendance (`present`\|`absent`). |
| `GET` | `/sessions/:id/log` | trainer, athlete (own) | Read log for session. |
| `POST` | `/sessions/:id/log` | athlete (own), trainer (any) | Append a `WorkoutLog` row. |
| `POST` | `/groups/:id/broadcast` | trainer | Send broadcast message to all members. |
| `GET` | `/athletes/:id/history?from&to` | trainer (own athletes), athlete (own) | Past sessions with logs. |

## Validation & state transitions

### Invariants
- A `User` row's `role` is immutable after creation.
- An `Invite` is redeemable iff `used_at IS NULL AND expires_at > now`.
- `personal` group has at most one membership with `status = active`.
- `Session.scheduled_at` is in the future at creation time; cancelling a past session is rejected.
- A `WorkoutLog` set_index is contiguous starting at 1 per `(session_id, athlete_id, exercise_id)`.
- An `Attendance` row may transition `present|absent` only after `session.scheduled_at`.

### State machines

- **Invite**: `created → used` (on redemption) | `created → expired` (lazy on read after `expires_at`).
- **Membership**: `pending → active` (on first athlete app open after invite redemption) | `active → removed` (trainer action).
- **Session**: `scheduled → completed` (when trainer marks attendance for the last athlete OR at `scheduled_at + duration_min + 24h`) | `scheduled → cancelled`.
- **Attendance**: `pending → confirmed | declined` (pre-session, by athlete) → `present | absent` (post-session, by trainer).
- **Notification**: `scheduled → sent` (on successful Telegram delivery) | `scheduled → cancelled` (if session cancelled).

### Authorization rules
- Trainer can read/write all entities scoped to their own groups, athletes, exercises, templates, sessions.
- Athlete can read sessions of groups they belong to, their own attendance, and their own logs.
- Athlete can write only their own attendance and own logs.
- `initData` HMAC validation is mandatory on every HTTP request; expired `initData` (> 24h since `auth_date`) is rejected.

## Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Stack choice (backend, storage, mini-app framework) not yet made | Blocks all dev | Task 01 produces an Architecture Decision document with explicit choice; PRD-02+ inherits it. |
| `initData` HMAC mis-validation lets attackers impersonate users | Critical security | Validation library covered by unit tests using Telegram-provided sample payloads; one-line auth middleware applied to every route by default. |
| Recurring sessions expand to many DB rows; reminders mis-fire on DST | Reminder spam or missed reminders | Store `recurrence_rule` as RRULE; materialize only the next 60 days; reminder scheduler runs hourly, idempotent on `(user_id, session_id, kind, scheduled_at)`. |
| Mini-App opens slowly on weak mobile networks | Trainer/athlete abandon | Mini-App bundle ≤ 250 KB gz; offline-friendly shell; non-blocking auth. |
| Personal-group "1 athlete" invariant violated by race on invite redemption | Wrong athlete attached to personal program | Redemption is a single transactional `INSERT … WHERE NOT EXISTS (… active member of personal group)`. |
| Trainer mass-broadcasts spam athletes | Athletes mute bot / churn | Rate-limit broadcasts to 5/day per group; show send confirmation with member count. |
| Naming clash on Telegram (`@your_coach_bot` taken) | Brand placeholder breaks at launch | Naming sub-task in Task 01 reserves bot username and Mini-App brand before any production deploy. |
| Telegram WebApp API changes break Mini-App | Mini-App offline | Pin to documented stable `initData` contract; integration test against current Telegram desktop and iOS clients before each release. |

## Acceptance criteria

The full set lives in the delta specs under `prd_01_bot-and-mini-app-mvp/specs/`. The PRD is accepted when, against a fresh deployment seeded only with a trainer Telegram account:

1. The trainer can complete `/start` and reach the Mini-App with role `trainer` in ≤ 2 minutes.
2. The trainer can create a group, generate an invite link, and an athlete can join via that link in ≤ 1 minute end-to-end.
3. The trainer can create an exercise catalog (≥ 3 exercises), a workout template (≥ 1 exercise, ≥ 2 sets each), and schedule a one-off session for tomorrow with that template.
4. The trainer can also schedule a weekly-recurring session and see the next 4 occurrences in the Mini-App calendar.
5. The athlete receives a reminder ~24h and ~1h before the session and can confirm attendance from the message.
6. After the session, the athlete logs at least one set per assigned exercise from the Mini-App; the trainer sees the logs in the session detail.
7. The trainer marks attendance (`present`/`absent`) for each athlete; the session transitions to `completed`.
8. The trainer can broadcast a text message to the group; every active member receives it.
9. The trainer can open an athlete's history and see all past sessions with logs and attendance.
10. All 9 living specs (one per domain) are seeded on archive of this PRD with `ADDED` requirements matching items 1-9.
