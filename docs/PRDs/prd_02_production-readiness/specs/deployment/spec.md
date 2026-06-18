# deployment — delta for PRD-02

## ADDED Requirements

### Requirement: A single Docker image carries the whole service
The build MUST produce one container image that, on `docker run`, exposes the HTTP API, dispatches the Telegram bot (via webhook in production), and runs the notification worker — in one process.

#### Scenario: Local docker run
- GIVEN a clean machine with Docker installed
- WHEN the developer runs `docker build -t trainbeat . && docker run -p 8000:8000 -e DATABASE_URL=... -e TELEGRAM_BOT_TOKEN=... trainbeat`
- THEN `curl http://localhost:8000/healthz` returns `{"status":"ok"}` within 10 seconds

#### Scenario: Image size budget
- GIVEN the production Docker image
- WHEN the build finishes
- THEN the image size is ≤ 400 MB uncompressed

### Requirement: Service is reachable over public HTTPS after deploy
The deploy pipeline MUST produce a public HTTPS URL (`https://<app-name>.fly.dev` by default) that responds `200 OK` at `/healthz` within 5 minutes of `flyctl deploy` completing.

#### Scenario: Smoke check after deploy
- GIVEN a successful `flyctl deploy` run
- WHEN the deploy GitHub Action's smoke step hits `https://<app-name>.fly.dev/healthz`
- THEN the response status is `200` and body is `{"status":"ok"}`
- AND the action exits 0; otherwise it exits 1 and the build is marked failed

### Requirement: Secrets are managed by the host, never committed
Production secrets (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `DATABASE_URL`) MUST be set via `flyctl secrets set` (or equivalent) and MUST NOT appear in source, Docker image layers, or CI logs.

#### Scenario: Repo scan
- GIVEN the repository at any commit
- WHEN a grep scan looks for the literal pattern of a Telegram token (`\d{8,10}:[A-Za-z0-9_-]{30,}`) across tracked files
- THEN zero matches are found

#### Scenario: CI log redaction
- GIVEN the deploy GitHub Action with `TELEGRAM_BOT_TOKEN` set as a repository secret
- WHEN the job runs
- THEN the action logs do not contain the token value (masked by Actions' secret redaction)

### Requirement: Telegram updates arrive via webhook in production
In production the bot MUST receive updates through `POST /api/telegram/webhook` authenticated by the `X-Telegram-Bot-Api-Secret-Token` header; long-polling MUST be disabled.

#### Scenario: Webhook configured after deploy
- GIVEN a successful deploy
- WHEN `scripts/botfather_setup.py` runs against the production URL
- THEN `getWebhookInfo` returns the production `/api/telegram/webhook` URL with `pending_update_count` ≤ some threshold
- AND a subsequent `/start` from a test account is dispatched and replied to within 5 seconds

#### Scenario: Missing or wrong secret token rejected
- GIVEN the production webhook endpoint
- WHEN a request arrives without `X-Telegram-Bot-Api-Secret-Token` or with a mismatched value
- THEN the response is `401` and no update is processed

### Requirement: The notification worker delivers reminders without manual intervention
A scheduler MUST run inside the deployed process and MUST call the existing `deliver_due` sweep no less than once per 15 minutes; reminders MUST be delivered within (1h + 15min) of their `scheduled_at`.

#### Scenario: Reminder fires automatically
- GIVEN a deployed instance with a session scheduled for `now + 70 minutes` and reminders scheduled at `now + 70` and `now + 10` minutes
- WHEN 25 minutes elapse from `now + 10`
- THEN the 1-hour reminder has `status = sent` and `sent_at` is within 15 minutes of the scheduled offset

#### Scenario: Worker survives a single delivery failure
- GIVEN a reminder whose Telegram send raises a transient error
- WHEN the worker's next tick runs
- THEN the row is still `status = scheduled` (not flipped to `sent`) and will be re-attempted on the following tick

### Requirement: Health endpoint reports liveness and DB connectivity
`/healthz` MUST return `200 OK` for liveness without depending on the database; `/readyz` MUST attempt a trivial DB query and return `200` only if it succeeds, otherwise `503`.

#### Scenario: Liveness without DB
- GIVEN the process running with the database unreachable
- WHEN `/healthz` is hit
- THEN the response status is `200` and body is `{"status":"ok"}`

#### Scenario: Readiness with DB down
- GIVEN the same condition
- WHEN `/readyz` is hit
- THEN the response status is `503` and the body identifies the database as unavailable
