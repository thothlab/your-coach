# deployment — living spec

## Requirements

### Requirement: A single Docker image carries the whole service
The build MUST produce one container image that, on `docker run`, exposes the HTTP API, dispatches the Telegram bot, and runs the notification worker — in one process.

#### Scenario: Local docker run
- GIVEN a clean machine with Docker installed
- WHEN the developer runs `docker build -t trainbeat . && docker run -p 8000:8000 -e DATABASE_URL=... -e TELEGRAM_BOT_TOKEN=... trainbeat`
- THEN `curl http://localhost:8000/healthz` returns `{"status":"ok"}` within 10 seconds

#### Scenario: Image size budget
- GIVEN the production Docker image
- WHEN the build finishes
- THEN the image size is ≤ 400 MB uncompressed

### Requirement: Service is reachable over public HTTPS through the VPS TLS front
Production runs on the Mac Mini home server, fronted by Caddy on the existing VPS (`devipad.ru`) over an SSH reverse tunnel. The public host `trainbeat.devipad.ru` MUST respond `200 OK` at `/healthz` whenever the Mac Mini stack is healthy and the tunnel is up.

#### Scenario: Public reachability through Caddy + tunnel
- GIVEN the Mac Mini `docker compose` stack is running and the SSH reverse tunnel from Mac Mini → VPS:8100 is established
- WHEN any client hits `https://trainbeat.devipad.ru/healthz`
- THEN the response status is `200` and body is `{"status":"ok"}`

#### Scenario: Tunnel auto-recovery
- GIVEN the autossh launchd agent on the Mac Mini owns the reverse tunnel
- WHEN the SSH connection drops (network blip, VPS reload)
- THEN autossh re-establishes the tunnel within 30 seconds without manual intervention

### Requirement: Secrets are managed on the host, never committed
Production secrets (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` if used, `DATABASE_URL`) MUST live in the Mac Mini's `.env` file (gitignored) and MUST NOT appear in source, Docker image layers, or CI logs.

#### Scenario: Repo scan
- GIVEN the repository at any commit
- WHEN a grep scan looks for the literal pattern of a Telegram token (`\d{8,10}:[A-Za-z0-9_-]{30,}`) across tracked files
- THEN zero matches are found

### Requirement: Telegram updates arrive via long-polling by default
The bot MUST receive Telegram updates via `getUpdates` (long-polling) in the default configuration. The webhook handler (`POST /api/telegram/webhook`) remains implemented and tested, but is only active when `BOT_MODE=webhook`.

#### Scenario: Bot connects without an inbound webhook
- GIVEN a fresh deployment with `BOT_MODE=polling` (default) and no webhook configured in BotFather
- WHEN the process starts
- THEN logs show `bot polling started` and the bot replies to `/start` from a test account within 5 seconds

#### Scenario: Webhook opt-in
- GIVEN `BOT_MODE=webhook` is set in `.env` AND `SETUP_WEBHOOK=1 python scripts/botfather_setup.py` has been run
- WHEN Telegram delivers an update to `https://trainbeat.devipad.ru/api/telegram/webhook` with the configured `X-Telegram-Bot-Api-Secret-Token`
- THEN the update is dispatched and a reply is sent within 5 seconds

#### Scenario: Missing or wrong secret token rejected on the webhook
- GIVEN the webhook endpoint is exposed
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
