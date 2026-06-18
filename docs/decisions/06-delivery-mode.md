# Decision 06 — Telegram delivery mode (PRD-02, revised)

**Date:** 2026-06-18
**Status:** Accepted (supersedes the webhook-in-prod draft once hosting moved to Mac Mini home-server in ADR-05)

## Decision

The bot uses **Telegram long-polling in every environment** (dev and prod). The webhook endpoint (`POST /api/telegram/webhook`) stays implemented and tested, gated behind `BOT_MODE=webhook`, but the default is polling.

## Rationale

- The Mac Mini outbound-connects to `api.telegram.org`; no inbound HTTPS needed for the bot to work. This frees the bot from the VPS Caddy + reverse-tunnel hop — bot↔Telegram keeps working even when the public domain is briefly down.
- The Mini-App still needs the public HTTPS domain (`trainbeat.devipad.ru`), but the bot doesn't. Separating those failure domains is a free win.
- Webhook code is kept (one file + tests) so flipping `BOT_MODE` switches modes without code changes — useful when we eventually want lower latency on bot updates or scale to multiple instances.

## Rejected

- **Webhook in prod.** Would tie the bot's liveness to the VPS Caddy + tunnel chain. Adds operational coupling for marginal latency benefit at MVP scale.
- **Hybrid (poll + webhook fall-back).** Telegram only honors one mode per token at any time. Mixing is not possible without surgically `deleteWebhook`/`setWebhook` between modes; not worth it.

## Consequences

- `scripts/botfather_setup.py` does **not** call `setWebhook` in the default flow. It only sets the command list and menu button. If `BOT_MODE=webhook` is chosen later, run the script with `SETUP_WEBHOOK=1` to call `setWebhook` too (the script reads that env flag).
- `TELEGRAM_WEBHOOK_SECRET` becomes optional. Kept in `.env.example` for the day someone switches to webhook mode.
- `__main__.py` chooses between `_serve_polling` and `_serve_webhook` based on `settings.bot_mode` (default `polling`).
