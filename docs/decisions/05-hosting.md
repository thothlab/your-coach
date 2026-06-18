# Decision 05 — Hosting (PRD-02)

**Date:** 2026-06-18
**Status:** Accepted

## Decision

Production runs on **Fly.io** as a single Machine in a single region (Amsterdam, `ams`), with **Fly Postgres** attached as the managed database. The single Machine carries the FastAPI HTTP API, the aiogram webhook dispatcher, and the apscheduler notification worker — all in one Python process.

## Rationale

- Fly's free-of-cold-start machines pair well with the in-process scheduler — `auto_stop_machines = false` keeps the worker alive without a separate cron service.
- Single-region single-machine is sufficient for the first paying trainer (≤ 100 athletes). Multi-region or autoscaling is not yet justified.
- Fly Postgres is one `fly pg create && fly pg attach` away; no extra account, no payment integration.
- Free TLS/HTTPS via Fly's auto-cert on the `*.fly.dev` subdomain — unblocks BotFather menu button without buying a domain.

## Rejected

- **Render** — cheaper hobby tier but worker tasks require a separate "Background worker" service, splitting the process model.
- **Railway** — similar to Render; pricing changes have been volatile recently.
- **Fly Machines split (api machine + worker machine)** — operationally cleaner for outage isolation, but doubles the cost and adds inter-process state to reason about. Deferred to a future PRD if a real reason emerges.

## Consequences

- One outage = bot + API + worker all down. Acceptable for MVP traffic; documented in the README runbook.
- `fly launch` is a one-time interactive step the user runs manually; subsequent `fly deploy` is non-interactive and triggered by CI.
- Secrets live in Fly (`fly secrets set …`); GitHub Action only needs `FLY_API_TOKEN` (deploy auth).

## First-time setup runbook

```bash
fly auth login                       # opens a browser; one-time per dev
fly launch --no-deploy               # answer prompts; uses fly.toml
fly pg create --name trainbeat-db    # answer prompts for region / size
fly pg attach --app trainbeat trainbeat-db   # sets DATABASE_URL secret
fly secrets set \
  TELEGRAM_BOT_TOKEN=<...> \
  TELEGRAM_WEBHOOK_SECRET=$(openssl rand -hex 32) \
  TELEGRAM_BOT_USERNAME=trainbeat_bot \
  TELEGRAM_WEBAPP_URL=https://<app>.fly.dev/ \
  PUBLIC_BASE_URL=https://<app>.fly.dev
fly deploy                           # first manual deploy
PUBLIC_BASE_URL=https://<app>.fly.dev \
  TELEGRAM_BOT_TOKEN=<...> \
  TELEGRAM_WEBHOOK_SECRET=<...> \
  python scripts/botfather_setup.py
```

Set repository secret `FLY_API_TOKEN` (from `fly auth token`) so the GitHub Action can `fly deploy` on push.
