# Decision 06 — Telegram delivery mode (PRD-02)

**Date:** 2026-06-18
**Status:** Accepted

## Decision

In **production** the bot receives updates via **webhook** (`POST /api/telegram/webhook`) authenticated by `X-Telegram-Bot-Api-Secret-Token`. In **development** (`APP_ENV=dev`) the bot uses long-polling.

## Rationale

- Fly's machine model assumes the process is reachable over HTTPS — webhooks are the natural fit. Long-polling would still work but burns CPU on idle.
- Webhook + secret token gives us first-class request authentication without writing our own JWT/HMAC layer.
- Telegram delivers updates with retries on 5xx, providing free at-least-once semantics for the bot path.

## Rejected

- **Long-polling in production** — works but is wasteful on a machine that already serves HTTP; harder to scale beyond one machine; we'd lose the implicit request-trace baseline.
- **Hybrid (polling + webhook)** — Telegram only accepts one mode at a time per token; trying to mix risks "wrong number of pending updates" diagnostics that consume time.

## Consequences

- Bot is only reachable while the Fly machine is up and the public URL resolves. (Acceptable; same as the API.)
- Switching modes requires `setWebhook` / `deleteWebhook` calls — encoded in `scripts/botfather_setup.py` (sets webhook) and a documented `flyctl ssh console` snippet to delete it when reverting to polling for local debug.
- The `APP_ENV` flag is the single switch — no separate `BOT_MODE` env to reason about.
