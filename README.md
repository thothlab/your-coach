# TrainBeat

Telegram-native fitness coaching: a bot + Mini-App for trainers running group and personal training.

- Backend: Python 3.12 + aiogram 3 + FastAPI + PostgreSQL — see [decision 01](docs/decisions/01-stack.md)
- Storage: PostgreSQL 16 — see [decision 02](docs/decisions/02-storage.md)
- Mini-App: SolidJS + Vite — see [decision 03](docs/decisions/03-mini-app-stack.md)
- Brand: TrainBeat, bot `@trainbeat_bot` — see [decision 04](docs/decisions/04-naming.md)

The active PRD and specs live under `docs/PRDs/prd_01_bot-and-mini-app-mvp/`.

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (for local Postgres)

## First-time setup

```bash
cp .env.example .env
# fill TELEGRAM_BOT_TOKEN from @BotFather
make install
```

## Daily development

```bash
make dev    # starts Postgres, bot poller, FastAPI on :8000, Vite dev on :5173
make test
make lint
make fmt
```

## Build

```bash
make build  # builds Mini-App and verifies the 250 KB gz bundle budget
```

## Layout

```
backend/            Python service (bot + HTTP API)
  src/trainbeat/    Package root
  tests/            Pytest suite
mini-app/           Telegram WebApp (SolidJS)
  src/              App source
  scripts/          Bundle-size check
docs/
  PRDs/             Active PRDs (planning + delta specs + tasks)
  decisions/        Architecture decision records
  specs/            Living source-of-truth specs (created on PRD archive)
  Archive/          Closed PRDs after archive merge
.github/workflows/  CI
docker-compose.yml  Local Postgres
Makefile            One entry point for dev/test/lint/build
```
