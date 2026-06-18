#!/usr/bin/env bash
# TrainBeat — one-shot Mac Mini bootstrap.
#
# Usage:
#   1. Copy this script to the Mac Mini (e.g. via scp or paste into a file)
#   2. export TELEGRAM_BOT_TOKEN=<your_botfather_token>
#   3. bash setup-mac-mini.sh
#
# Idempotent: re-running pulls the latest main, rebuilds, re-applies the
# launchd unit.

set -euo pipefail

REPO_URL="https://github.com/thothlab/your-coach.git"
PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/your-coach}"
VPS_HOST="${VPS_HOST:-153.80.185.242}"
VPS_PORT="${VPS_PORT:-58222}"
VPS_USER="${VPS_USER:-tunnel}"
TUNNEL_REMOTE_PORT="${TUNNEL_REMOTE_PORT:-8100}"
TUNNEL_LOCAL_PORT="${TUNNEL_LOCAL_PORT:-8000}"

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "set TELEGRAM_BOT_TOKEN before running this script" >&2
  exit 1
fi

echo "==> [1/6] clone or pull repo"
mkdir -p "$(dirname "$PROJECT_DIR")"
if [ ! -d "$PROJECT_DIR/.git" ]; then
  git clone "$REPO_URL" "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"
git fetch --all
git checkout main
git pull --ff-only

echo "==> [2/6] write .env (gitignored)"
cat > .env <<EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_USERNAME=trainbeat_bot
TELEGRAM_WEBAPP_URL=https://trainbeat.devipad.ru/
PUBLIC_BASE_URL=https://trainbeat.devipad.ru
DATABASE_URL=postgresql+asyncpg://trainbeat:trainbeat@db:5432/trainbeat
APP_ENV=prod
BOT_MODE=polling
SCHEDULER_INTERVAL_MINUTES=15
EOF
chmod 600 .env

echo "==> [3/6] docker compose up"
if ! docker info >/dev/null 2>&1; then
  echo "docker is not running — start Docker Desktop / colima first" >&2
  exit 1
fi
docker compose -f deploy/docker-compose.prod.yml up -d --build
echo "waiting for app to become healthy..."
for i in $(seq 1 30); do
  if curl -fsS http://localhost:${TUNNEL_LOCAL_PORT}/healthz >/dev/null 2>&1; then
    echo "  healthz OK after ${i}s"
    break
  fi
  sleep 2
done

echo "==> [4/6] alembic migrations"
docker compose -f deploy/docker-compose.prod.yml exec -T app \
  python -m alembic -c /app/backend/alembic.ini upgrade head

echo "==> [5/6] autossh + launchd"
if ! command -v autossh >/dev/null; then
  if command -v brew >/dev/null; then
    brew install autossh
  else
    echo "install Homebrew or autossh manually; aborting" >&2
    exit 1
  fi
fi
AUTOSSH_BIN=$(command -v autossh)

PLIST="$HOME/Library/LaunchAgents/com.trainbeat.tunnel.plist"
sed "s#/opt/homebrew/bin/autossh#${AUTOSSH_BIN}#" deploy/com.trainbeat.tunnel.plist > "$PLIST"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"
echo "tunnel plist loaded: $PLIST"

echo "==> [6/6] verify tunnel from VPS"
sleep 5
# This step assumes SSH access to the VPS from the Mac Mini.
# If it doesn't, run the listed command manually from your laptop.
echo "from the VPS, run: ss -tlnp | grep ${TUNNEL_REMOTE_PORT}"
echo
echo "DONE. Next:"
echo "  1. Make sure DNS A record exists: trainbeat.devipad.ru → 153.80.185.242"
echo "  2. From any machine with the bot token, run:"
echo "       TELEGRAM_BOT_TOKEN=... PUBLIC_BASE_URL=https://trainbeat.devipad.ru \\"
echo "         python scripts/botfather_setup.py"
echo "  3. curl https://trainbeat.devipad.ru/healthz"
