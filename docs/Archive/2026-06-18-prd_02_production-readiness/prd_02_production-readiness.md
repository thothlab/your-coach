# PRD-02 — Production readiness

## Objective

Take the PRD-01 MVP from "runs on my laptop with docker compose" to a state where a real trainer opens the Mini-App from Telegram, schedules a session, and gets reminders without anyone running a command on a developer machine.

Success = (a) `git push origin main` deploys to a live host, (b) Telegram clients reach the live Mini-App through BotFather's menu button, (c) reminders fire automatically at the spec'd offsets, (d) the trainer can do every PRD-01 workflow from the Mini-App without touching the HTTP API directly.

## Non-objectives

- Payments / subscriptions (candidate PRD-03)
- Native iOS / Android apps; standalone web app outside Telegram
- Video uploads, video coaching, AI-generated workouts
- Multi-trainer / gym mode / organization roles
- Custom domain purchase — Fly's `*.fly.dev` subdomain is acceptable until a brand domain is bought separately
- Sentry / external error reporting — stdout logs for PRD-02; PRD-03 candidate
- Horizontal scaling — single process is acceptable for first paying trainer (≤ 100 athletes total)

## Data model

No new entities. PRD-02 is operational + UI.

The existing model from PRD-01 is sufficient. The notification worker reads `Notification` rows already written by `/api/sessions` handlers.

## API list

### New endpoints

| Method | Path | Caller | Purpose |
|---|---|---|---|
| `POST` | `/api/telegram/webhook` | Telegram servers | Receive bot updates (replaces long-polling in production). Body validated by Telegram secret token header. |
| `GET` | `/` and `/assets/*` | Mini-App static | FastAPI serves the built Mini-App `index.html` and asset chunks. |

### Existing endpoints — unchanged contracts

All PRD-01 endpoints stay; consumed unchanged by the expanded Mini-App.

## Validation & state transitions

### Webhook auth
- Telegram MUST include `X-Telegram-Bot-Api-Secret-Token` matching `TELEGRAM_WEBHOOK_SECRET` env var; mismatched or missing token returns `401` and the update is dropped.
- The webhook secret is randomly generated at deploy time and set via `fly secrets set TELEGRAM_WEBHOOK_SECRET=...` plus `setWebhook(secret_token=...)`.

### Telegram delivery mode (production)
- Long-polling (`dp.start_polling`) MUST NOT run in production; the bot dispatches incoming `Update` objects from webhook payloads.
- Locally, `make dev` keeps polling for ease of development.

### Scheduler invariants
- The apscheduler job MUST be idempotent against the existing `Notification` unique constraint (PRD-01).
- The job MUST NOT block FastAPI request handling for more than 1 second per tick (batched to 500 rows max, async Telegram client).
- If the scheduler is restarted mid-tick, any unmarked rows are picked up on the next tick (no in-flight registry needed — DB row state is the source of truth).

### `/invite` multi-group selection
- When a trainer has ≥ 2 groups, `/invite` MUST reply with an inline keyboard listing each group by name; a per-message callback ID identifies the chosen group; on tap, the bot generates and replies the invite URL.
- The selection state MUST expire after 5 minutes; tapping after that returns "selection expired".

### Mini-App creation forms
- All trainer-creation POSTs go through the existing `/api/*` endpoints with the same validation as PRD-01.
- The forms MUST disable Submit until required fields are valid (client-side); server validation errors MUST be surfaced inline near the offending field.

## Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Webhook URL must be HTTPS-reachable, requires Fly's auto-TLS to be working before first webhook update | Bot silent in production | Smoke step in deploy job hits `/healthz` over HTTPS post-deploy; deploy fails on non-200 |
| Single process couples bot + API + worker — one crash kills all | Outage cascades | Documented runbook; Fly auto-restart; PRD-03 can split into separate machines |
| Fly Postgres free tier sleep / cold-start | First request after idle is slow | Hobby plan minimum; periodic self-ping disabled (out of scope for now) |
| Apscheduler ticks share the event loop with handlers | Sweep can starve incoming requests | Batch 500 max, await Telegram in parallel via `asyncio.gather`, keep sweep < 1 s in tests |
| Trainer leaves `/invite` callback open for hours | Stale state in memory if FSM in RAM | Use aiogram MemoryStorage with key TTL ≤ 5 min OR encode group_id directly in callback_data (no FSM state) |
| BotFather steps still manual | New developer can't reproduce setup | `scripts/botfather_setup.py` reads env, calls setMyCommands + setMenuButton + setWebhook; documented in README |
| Mini-App router state in URL hash exposes routes Telegram doesn't expect | Telegram back-button confusion | Use `@solidjs/router` with memory router on Telegram (no URL changes); fallback to history on dev |
| Secret rotation (TELEGRAM_BOT_TOKEN refresh) | Requires re-set webhook | Bot startup re-sets webhook on token change (compare against `getWebhookInfo`); documented in runbook |
| `fly launch` is one-time, asks interactive questions | CI can't bootstrap | First-time setup done manually by user; subsequent `fly deploy` is non-interactive |

## Acceptance criteria

Full Given/When/Then in `prd_02_production-readiness/specs/`. The PRD is accepted when, on a fresh clone followed by `fly launch` (manual) and a push to `main`:

1. Docker image builds in ≤ 5 minutes and starts a process exposing `/healthz` returning `{"status":"ok"}` on `:8000` within 10 seconds.
2. `git push origin main` triggers CI; on CI green, the deploy job runs `flyctl deploy` and the resulting Fly app responds `200` at `https://<app>.fly.dev/healthz` within 5 minutes of push.
3. After `scripts/botfather_setup.py` runs once with the production URL, `setMyCommands` lists `/start /invite /app`, `getMenuButton` returns the production Mini-App URL, and `getWebhookInfo` returns the production webhook URL.
4. A `POST /api/sessions` with `scheduled_at = now + 65 minutes` results in exactly one delivered reminder Telegram message between 65 and 60 minutes from now (the 1-hour reminder) — verified by tail of structured logs.
5. A trainer with 3 groups sending `/invite` receives an inline keyboard with exactly 3 buttons; tapping any one replies with a fresh invite URL within 30 seconds.
6. From the Mini-App trainer home, "Create group" opens a form; submitting creates the group via `POST /api/groups`; the new group appears in the home list without a full page reload.
7. From the Mini-App, the trainer creates an exercise, then a workout template referencing it, then a session with that template scheduled for tomorrow — without leaving the Mini-App.
8. From the Mini-App, the trainer composes a broadcast for a group; on send, the response shows `recipient_count`; the next sixth broadcast within 24h surfaces a "rate limit" error inline (no crash).
9. The Mini-App initial bundle remains ≤ 250 KB gzipped after all new screens (CI check unchanged).
