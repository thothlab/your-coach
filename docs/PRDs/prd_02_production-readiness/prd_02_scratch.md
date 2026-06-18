# prd_02_scratch — Production readiness

## Problem & target users
- **Real trainer (first paying customer)** needs the MVP to actually run somewhere — open Mini-App from Telegram, get reminders at 24h and 1h, manage clients without using a curl/REST tool.
- Today: PRD-01 backend + Mini-App work locally but nothing public. Reminders sit in DB; nobody calls `deliver_due`. Trainer can't create groups/exercises/workouts/sessions from UI (only via API).

## Scope

**In (PRD-02):**
- Containerization — single Docker image carrying FastAPI + aiogram polling + apscheduler worker + static Mini-App assets
- Hosting config — Fly.io app + Fly Postgres (or Neon, fallback); deploy GitHub Action
- BotFather production setup — automated post-deploy script: setMyCommands, setMenuButton (Mini-App URL), set webhook (if switching from long-polling)
- Notification worker — apscheduler AsyncIOScheduler running inside the main process; hourly job calls `deliver_due` with a real Telegram sender
- Extended bot `/invite` — aiogram FSM showing inline keyboard with the trainer's groups when there are 2+; auto-pick stays for single-group case
- Mini-App router (`@solidjs/router`) + reusable form primitives (Input, Select, FormShell)
- Trainer creation screens in Mini-App: GroupCreate, ExerciseCreate, WorkoutTemplateCreate, SessionCreate (with RRULE input), BroadcastCompose

**Out (future PRDs):**
- Payments / subscriptions
- Native mobile / standalone web apps beyond Mini-App
- Video / AI features
- Multi-trainer organizations
- Custom domain purchase (PRD-02 ships on Fly's `*.fly.dev` subdomain; user upgrades domain later)
- Sentry / error reporting (defer; logs to stdout for now)

## Domain model
No new domain entities — PRD-02 is operational + UI. Adds operational artifacts:
- Container image (`trainbeat:<sha>`)
- Fly app spec
- Deploy GitHub Action job
- Apscheduler in-process worker (no DB schema)

## API / integration needs
- **Telegram Bot API webhook** — production switches from long-polling to webhook (`/api/telegram/webhook`) to avoid hosting a long-running polling loop
- **Fly.io platform API** via `flyctl` (called from CI)
- **Telegram WebApp URL** — set in BotFather via `setMenuButton`

## Lifecycle / status model
No new lifecycles. The `Notification` lifecycle from PRD-01 keeps working, now driven by a real worker rather than test-invoked sweeps.

## Acceptance criteria (high level — full Given/When/Then in delta specs)
1. `docker build .` produces an image that runs `trainbeat serve` and exposes `/healthz` on `:8000`.
2. Pushing to `main` triggers a GitHub Action that runs CI then deploys to Fly.io if CI passes.
3. After deploy, the trainer can open `https://<bot>/?start=app` style in BotFather and reach the live Mini-App.
4. A session created via API gets two reminders, and the apscheduler worker delivers them within 1 minute of `scheduled_at`.
5. `/invite` with 2 groups shows an inline keyboard; trainer taps a group; bot replies with an invite link within 30 seconds.
6. Trainer can create a group from Mini-App; the group appears in the trainer-home list immediately after navigating back.
7. Trainer can create an exercise + workout template + session from Mini-App and have them visible to the assigned group's athletes.
8. Trainer can send a broadcast from Mini-App and see member-count confirmation; 6th broadcast within 24h returns `429`.

## Affected domains
- `bot-ui/` — MODIFIED requirement: `/invite` supports multi-group selection via FSM
- `mini-app/` — ADDED requirements: trainer-side creation screens, router contract
- `deployment/` — **NEW** living spec: availability, health endpoint, deploy lifecycle, secrets handling
- `notifications/` — no delta required (existing spec already mentions the scheduler; worker is implementation)

## Decisions to record as ADRs
- ADR 05: Hosting — Fly.io single-region single-process vs alternatives (Render, fly machines + separate worker, Railway)
- ADR 06: Telegram delivery mode — long-polling vs webhook in production
- ADR 07: Mini-App static delivery — served by FastAPI vs Cloudflare Pages

## Risks (to expand in PRD)
- Single-process model couples bot, API, worker — outage takes everything down. Mitigation: documented runbook; PRD-03+ candidate to split.
- Webhook requires public HTTPS; Fly provides via auto-cert. Mitigation: include cert verification in deploy DoD.
- Fly Postgres has rate / IO limits on free/cheap tier. Mitigation: pick a paid Hobby plan; document migration path to Neon.
- `apscheduler` AsyncIOScheduler shares the event loop with FastAPI + aiogram — long jobs starve handlers. Mitigation: keep `deliver_due` batched at 500, run hourly.
- BotFather steps are still manual — `setMenuButton` requires a real domain. Mitigation: ship a helper script `scripts/botfather_setup.py` invoked manually after first deploy.
