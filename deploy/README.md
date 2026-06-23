# Deploy runbook — Mac Mini (primary) + VPS Caddy (TLS front)

See `docs/decisions/05-hosting.md` for the architecture rationale.

## One-time setup

### On the VPS (`153.80.185.242` / `devipad.ru`)

1. Append the snippet to Caddy:
   ```bash
   ssh -p 58222 admin@153.80.185.242
   sudo bash -c 'cat >> /etc/caddy/Caddyfile' < deploy/Caddyfile.snippet
   sudo systemctl reload caddy
   ```
2. (If not already done.) Make sure the `tunnel` user accepts an SSH key from the Mac Mini and that UFW allows port 58222.

### On the Mac Mini (home server)

1. Clone the repo and create `.env`:
   ```bash
   git clone https://github.com/thothlab/your-coach.git
   cd your-coach
   cp .env.production.example .env
   # fill TELEGRAM_BOT_TOKEN (BotFather) and any overrides
   ```
2. Bring the stack up:
   ```bash
   docker compose -f deploy/docker-compose.prod.yml up -d --build
   docker compose -f deploy/docker-compose.prod.yml ps
   curl -fsS http://localhost:8000/healthz   # → {"status":"ok"}
   ```
3. Apply migrations:
   ```bash
   docker compose -f deploy/docker-compose.prod.yml exec app \
     python -m alembic -c /app/backend/alembic.ini upgrade head
   ```
4. Open the reverse tunnel as a launchd agent:
   ```bash
   brew install autossh
   cp deploy/com.trainbeat.tunnel.plist ~/Library/LaunchAgents/
   launchctl load -w ~/Library/LaunchAgents/com.trainbeat.tunnel.plist
   # verify the tunnel actually landed
   ssh -p 58222 admin@153.80.185.242 'ss -tlnp | grep 8100'
   ```
5. Verify external reachability:
   ```bash
   curl -fsS https://trainbeat.devipad.ru/healthz   # → {"status":"ok"}
   ```
6. Configure BotFather (commands + Mini-App menu button):
   ```bash
   TELEGRAM_BOT_TOKEN=<...> \
     PUBLIC_BASE_URL=https://trainbeat.devipad.ru \
     python scripts/botfather_setup.py
   ```

## Media storage channel

Exercise photos/videos are not stored on disk — the bot uploads them into a
private Telegram channel (`STORAGE_CHANNEL_ID` in `.env`) and we keep only the
Telegram file ids in Postgres. The channel is a hidden blob store.

Setup:
1. Create a Telegram **channel** and add the bot as an **administrator** (it
   needs "Post messages").
2. Get its numeric id (forward a post to `@userinfobot`, or read it from
   `getUpdates`) — it looks like `-1001234567890`.
3. Put it in `.env`: `STORAGE_CHANNEL_ID=-1001234567890`, then restart `app`.

**Keep the channel private — do not give it a public @username.** Membership in
this channel is separate from using the bot or the Mini-App, so normal users are
never added to it and cannot see it. But a *public* channel is discoverable by
search: anyone typing the @username could open it and browse the entire exercise
media library. A private (invite-only) channel cannot be found this way.

Verify it is private at any time (`username` must print `None`):
```bash
docker compose -f deploy/docker-compose.prod.yml exec app python -c \
"import asyncio; from aiogram import Bot; from trainbeat.config import settings
async def m():
    b = Bot(settings.telegram_bot_token)
    c = await b.get_chat(settings.storage_channel_id)
    print('username:', c.username)  # None = private (good); non-null = public (fix it)
    await b.session.close()
asyncio.run(m())"
```

Media reaches users without exposing the channel: photos are proxied/streamed
through the backend into the Mini-App; videos are re-sent into the user's own
private chat with the bot by file id.

## Day-to-day updates

```bash
ssh mac-mini
cd ~/projects/your-coach
git pull
docker compose -f deploy/docker-compose.prod.yml up -d --build
docker compose -f deploy/docker-compose.prod.yml exec app \
  python -m alembic -c /app/backend/alembic.ini upgrade head
```

(Wrap into a post-merge hook on a separate `production` checkout if you
want zero-touch updates after `git push`.)

## Bot mode

Default is long-polling (`BOT_MODE=polling`). The bot stays connected to
Telegram even if the VPS tunnel is briefly down; only the Mini-App needs
the public URL.

To switch to webhook mode (e.g. for multiple bot instances later):
1. Set `BOT_MODE=webhook` and `TELEGRAM_WEBHOOK_SECRET=...` in `.env`.
2. `docker compose ... up -d` to restart `app`.
3. Run `SETUP_WEBHOOK=1 TELEGRAM_WEBHOOK_SECRET=... PUBLIC_BASE_URL=... TELEGRAM_BOT_TOKEN=... python scripts/botfather_setup.py`.

## Health checks

- Bot health: `docker compose ... logs -f app | grep "bot polling started"`
- HTTP health: `curl https://trainbeat.devipad.ru/healthz`
- DB health: `curl https://trainbeat.devipad.ru/readyz`
- Tunnel health: `ss -tlnp | grep 8100` on the VPS (port should be listening)

## Backups

Postgres data lives in the `trainbeat-pg` Docker named volume on the Mac
Mini. Hook it into the home-server's existing backup routine (or `pg_dump`
nightly via launchd) — same pattern as the Immich Postgres volume.
