# Decision 05 — Hosting (PRD-02, revised)

**Date:** 2026-06-18
**Status:** Accepted (supersedes the Fly.io draft from the original PRD-02)

## Decision

Production runs on the **owner's Mac Mini** (home server already hosting Gitea, Jellyfin, Immich, Calibre-Web, FileBrowser, Navidrome). A pre-existing **VPS at `devipad.ru`** acts as a TLS front: Caddy on the VPS terminates HTTPS for `trainbeat.devipad.ru` and reverse-proxies into an SSH reverse-tunnel that the Mac Mini opens against the VPS — the same pattern already battle-tested by the other six self-hosted services.

Everything (FastAPI + aiogram + apscheduler + Postgres) runs on the Mac Mini via `docker compose`. Reverse-tunnel keeps the public surface limited to the VPS's existing TLS edge.

## Rationale

- **Cost = 0.** Both machines exist; no new hosting, no card, no managed PG bill.
- **Resources.** Mac Mini has plenty of RAM/CPU/disk; VPS has 2 GB RAM with Caddy + Xray + x-ui already eating into it.
- **Operational pattern already proven.** Caddy reverse-proxy → SSH reverse-tunnel → home service is the standard rig (`git.devipad.ru`, `video.devipad.ru`, etc.). Adding `trainbeat.devipad.ru` is one Caddyfile snippet and one tunnel.
- **TLS only where needed.** Telegram requires HTTPS for Mini-App URL and webhook; Caddy's auto-TLS on the VPS gives both without buying a separate domain.
- **Bot independence from public reachability.** Long-polling means the bot ↔ Telegram channel works even if the VPS or the tunnel is down; only Mini-App goes dark in that case.

## Rejected

- **Fly.io single-machine + Fly Postgres** — costs real money, second account to manage, redundant with home server. (This was the original PRD-02 plan; reversed once the existing VPS-tunnel infra surfaced.)
- **VPS-only deploy.** Fits but RAM is tight (1.7 GB free with Caddy + Xray) — leaves zero headroom for PG growth and one OOM takes Xray down too.
- **Cloudflare Tunnel.** Works but introduces a third-party dependency for something the SSH-tunnel pattern already solves natively.

## Architecture

```
                     Telegram clients
                          │
                  HTTPS  │   long-poll
                  443    │   getUpdates
                          ▼
┌──────────────── VPS (153.80.185.242) ────────────────┐
│  Caddy (auto-TLS for *.devipad.ru)                    │
│    trainbeat.devipad.ru → 127.0.0.1:8100              │
│    (8100 = SSH reverse-tunnel port from Mac Mini)     │
└────────────────────────┬──────────────────────────────┘
                          │  ssh -R 8100:localhost:8000
                          │  via autossh (Mac Mini → VPS)
                          ▼
┌──────────────── Mac Mini (home) ──────────────────────┐
│  docker compose:                                       │
│    app   → trainbeat:latest on :8000                   │
│    db    → postgres:16-alpine on :5432 (host-local)    │
│  outbound: bot polls Telegram, sends reminders         │
└────────────────────────────────────────────────────────┘
```

## Consequences

- **Single point of failure for Mini-App = home internet / Mac Mini.** Bot keeps working (long-poll), but Mini-App is unreachable. Acceptable for MVP traffic; matches the SLO of the other self-hosted services.
- **No CI deploy job.** Deploy is a `git pull && docker compose up -d --build` on the Mac Mini, optionally wrapped in a post-merge hook on the home-side clone. Adding remote SSH-deploy from GitHub Actions would punch a hole into the home network for marginal benefit — deferred.
- **Postgres is local to Mac Mini.** Backups are the home server's existing backup routine; document the location in `deploy/README.md`.
- **VPS Caddyfile picks up one extra snippet.** Already conventional — see `deploy/Caddyfile.snippet`.

## First-time setup runbook (high level)

See `deploy/README.md` for the exact commands. Short form:

1. On the VPS: append `deploy/Caddyfile.snippet` to `/etc/caddy/Caddyfile`, reload Caddy.
2. On the Mac Mini: `git clone`, fill `.env`, `docker compose -f deploy/docker-compose.prod.yml up -d --build`.
3. Mac Mini: launch a persistent `autossh -R 8100:localhost:8000 tunnel@devipad.ru -p 58222` (systemd/launchd unit).
4. Anywhere with the token: `python scripts/botfather_setup.py` — sets command list and menu button to `https://trainbeat.devipad.ru/`.
