# prd_01_scratch — Bot + Mini-App MVP

## Problem & target users
- **Trainer** (fitness coach): manages clients — group classes and personal training. Today tracks schedule and results in Notes / Excel / WhatsApp. No purpose-built tool inside Telegram, where clients already live.
- **Athlete** (client of trainer): wants to see schedule, confirm attendance, log workout results without installing another app. Already on Telegram.

## Scope

**In (PRD-01):**
- Telegram bot — entry point, commands, deep links, notifications
- Telegram Mini-App (WebApp) — schedule, session detail, result logging, history
- Trainer onboarding via `/start`
- Single-use invite links to bring athletes onboard
- Groups of athletes; "personal" group = 1 athlete
- Sessions: one-off and weekly-recurring
- Workout templates: exercises + sets + targets
- Session execution: attendance + per-athlete result logging
- Notifications: pre-session reminders + trainer broadcasts
- Per-athlete workout history

**Out (future PRDs):**
- Payments / subscriptions
- Public marketplace of trainers
- Native mobile apps / standalone website
- Video uploads / video coaching
- AI workout generation
- Multi-trainer organizations / gym mode

## Domain model
- **User** — id, telegram_id, name, role (trainer|athlete), created_at
- **Group** — id, trainer_id, name, type (group|personal), created_at
- **Membership** — group_id, athlete_id, status (pending|active|removed), joined_at
- **Invite** — id, token, trainer_id, group_id, expires_at, used_at, used_by_user_id
- **Exercise** — id, trainer_id, name, unit (reps|seconds|meters|kg)
- **WorkoutTemplate** — id, trainer_id, name, items: ordered list of (exercise_id, sets, target_reps, target_weight)
- **Session** — id, group_id, workout_template_id?, scheduled_at, duration_min, recurrence_rule?, status (scheduled|completed|cancelled)
- **Attendance** — session_id, athlete_id, status (pending|confirmed|declined|present|absent)
- **WorkoutLog** — session_id, athlete_id, exercise_id, set_index, actual_reps, actual_weight, note
- **Notification** — id, user_id, session_id, kind (reminder|broadcast), scheduled_at, sent_at, payload

## API / integration needs
- **Telegram Bot API** — webhook, commands, inline keyboards, deep links (`https://t.me/<bot>?start=<token>`), message sending
- **Telegram WebApp API** — `initData` HMAC validation, MainButton, theme, `sendData`
- **Internal HTTP API** — auth via Telegram `initData`; CRUD over domain model
- **Internal scheduler** — cron-like dispatch of reminders

## Lifecycle / status model
- Invite: `created → used | expired`
- Membership: `pending → active → removed`
- Session: `scheduled → completed | cancelled`
- Attendance: `pending → confirmed | declined → present | absent`
- Notification: `scheduled → sent | cancelled`

## Acceptance criteria (high-level — full Given/When/Then in delta specs)
- Trainer completes onboarding from Telegram in ≤ 2 minutes
- Trainer creates an invite link in ≤ 30 s; athlete joins in ≤ 1 minute
- Trainer schedules a session and assigns a workout from Mini-App
- Athlete receives a reminder ~24h and ~1h before a session
- Athlete logs results for a workout from Mini-App during/after the session
- Trainer reviews attendance and per-athlete results for any past session

## Affected domains
PRD-01 seeds the first version of every living spec — all deltas are `ADDED`:
- `identity/` — users, roles, Telegram linkage
- `invites/` — invite link generation & redemption
- `groups/` — groups + personal-client memberships
- `scheduling/` — sessions, recurrence
- `workouts/` — exercise catalog, workout templates
- `sessions/` — attendance, result logging
- `notifications/` — reminders, broadcasts
- `bot-ui/` — bot interaction surface (commands, deep links, notifications)
- `mini-app/` — Telegram Mini-App UI surface

## Decisions deferred to Task-01 (bootstrap)
- Backend stack (Python + aiogram | Node + grammY | Go + telego)
- Storage (Postgres | SQLite for MVP)
- Mini-App stack (React + Vite | SolidJS | Svelte)
- Hosting
- Branding: bot `@username` + Mini-App name (placeholder: "your-coach")
