# Task 03 — BotFather production setup

## Goal
A repeatable script that, given a deployed URL, configures BotFather: command menu, menu button (Mini-App URL), webhook (with secret). Runs manually once after first deploy; idempotent for re-runs.

## Scope
**In:** `scripts/botfather_setup.py`, README section documenting when to run it.
**Out:** automating the `fly launch` flow.

## Subtasks
1. `scripts/botfather_setup.py` reads `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, and `PUBLIC_BASE_URL` from env (or CLI args).
2. Calls Telegram Bot API methods via `httpx`:
   - `setMyCommands` with `[/start, /invite, /app]` + descriptions
   - `setChatMenuButton` with `{type: web_app, text: "Open TrainBeat", web_app: {url: <base>/}}` so the Mini-App opens via the chat menu icon
   - `setWebhook(url=<base>/api/telegram/webhook, secret_token=<secret>)`
3. Verifies via `getWebhookInfo` that the registered URL matches.
4. Re-running is idempotent (same input → same effective state).

## Deliverables
- `scripts/botfather_setup.py`
- `scripts/__init__.py` if needed
- `README.md` — UPDATE: "Post-deploy: BotFather setup" section

## Definition of Done
- [ ] `python scripts/botfather_setup.py` reads env, exits 0 on success
- [ ] `getMyCommands` returns the configured list after run
- [ ] `getMenuButton` returns the Mini-App URL after run
- [ ] `getWebhookInfo` matches the configured URL after run
- [ ] Re-running the script twice in a row exits 0 both times with no error

## Tests
Tied to `specs/deployment/spec.md`:
- "Webhook configured after deploy"

## Dependencies
Task 01 (webhook endpoint), Task 02 (deployed URL).
