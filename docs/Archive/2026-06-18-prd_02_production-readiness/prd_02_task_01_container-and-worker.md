# Task 01 — Container + in-process worker

## Goal
Produce a single Docker image that, when run, exposes the HTTP API, dispatches the bot via webhook (or polling locally), and runs the notification worker on an internal schedule. After this task, `docker run trainbeat` is the only operational primitive needed for everything below.

## Scope
**In:** Dockerfile (multi-stage, builds Mini-App + installs backend), `/api/telegram/webhook` endpoint, `apscheduler` integration around `deliver_due`, `/readyz` endpoint, structured stdout logging.
**Out:** Fly.io specifics (Task 02), BotFather scripting (Task 03).

## Subtasks
1. Multi-stage `Dockerfile`: stage A builds Mini-App (`npm run build`); stage B installs Python deps + copies built static into a known path; final image entrypoint runs `python -m trainbeat serve`.
2. Add `serve` subcommand to `trainbeat.__main__`: based on `APP_ENV`, choose polling (dev) or webhook (prod); start uvicorn + scheduler in same event loop.
3. `apscheduler` `AsyncIOScheduler` job: every 15 minutes invoke `notification_repo.deliver_due(session, sender=telegram_send)`.
4. `telegram_send(user_id, payload)` — adapter that resolves user → telegram_id (via `User` row) and posts a Telegram message; honors aiogram bot instance.
5. `POST /api/telegram/webhook`: validates `X-Telegram-Bot-Api-Secret-Token`, parses `Update`, feeds into aiogram dispatcher.
6. `/readyz`: tries `SELECT 1` against the engine; returns 200 / 503.
7. Mount static Mini-App at `/` and `/assets/*` from FastAPI when files exist.
8. Add `python-json-logger` and switch `logging.basicConfig` to JSON output for prod (text for dev).

## Deliverables
- `Dockerfile` (root)
- `.dockerignore`
- `backend/src/trainbeat/__main__.py` — UPDATE: `serve` subcommand + scheduler integration
- `backend/src/trainbeat/api/webhook.py` — webhook handler
- `backend/src/trainbeat/scheduler.py` — apscheduler bootstrap
- `backend/src/trainbeat/telegram_sender.py` — adapter
- `backend/src/trainbeat/api/health.py` — `/healthz` + `/readyz`
- `backend/src/trainbeat/main.py` — UPDATE: include health + webhook routers, mount static
- Updates to `pyproject.toml` (`apscheduler>=3.10`, `python-json-logger>=2.0`)

## Definition of Done
- [ ] `docker build -t trainbeat .` succeeds in CI in ≤ 5 minutes
- [ ] `docker run -e APP_ENV=dev -e TELEGRAM_BOT_TOKEN=test -e DATABASE_URL=... trainbeat` exposes `/healthz` returning 200
- [ ] `/readyz` returns 200 when DB reachable, 503 when not (tested by killing PG in docker compose)
- [ ] Image size ≤ 400 MB uncompressed (CI check)
- [ ] Webhook endpoint returns 401 on missing secret; 200 on correct
- [ ] Scheduler delivers a due reminder within 15 minutes of scheduled_at when running locally

## Tests
Tied to `specs/deployment/spec.md` scenarios:
- "Local docker run"
- "Image size budget"
- "Missing or wrong secret token rejected"
- "Reminder fires automatically" (manual local verification — 5-min wait test)
- "Worker survives a single delivery failure" (unit test with stubbed sender)
- "Liveness without DB" / "Readiness with DB down" (integration tests)

## Dependencies
None (within PRD-02; depends on PRD-01 being merged).
