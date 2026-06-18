# Decision 01 — Backend stack

**Date:** 2026-06-18
**Status:** Accepted

## Decision

Backend stack for the bot and HTTP API is **Python 3.12 + aiogram 3 + FastAPI**, running under **uvicorn**, with **SQLAlchemy 2 (async) + Alembic** for persistence and **pydantic-settings** for configuration.

## Rationale

- **aiogram 3** is the mature, idiomatic async wrapper over the Telegram Bot API, with first-class support for inline keyboards, WebApp launch buttons, and FSM (useful for the `/invite` group-selection flow).
- **FastAPI** gives an OpenAPI schema out of the box — Mini-App can generate a typed client from it.
- Shared event loop between aiogram polling/webhook and FastAPI under uvicorn — one process can run both for MVP.
- Fast dev cycle, low ceremony.

## Rejected

- **Node.js + grammY + Hono** — TypeScript end-to-end was tempting, but the dev-team familiarity bias toward Python plus aiogram's deeper feature set won out.
- **Kotlin + Ktor** — would shine if native KMP clients were on the near-term roadmap; PRD-01 explicitly scopes them out.
- **Go + telego + chi** — operationally simple, but ecosystem around Telegram WebApp tooling is thinner and dev cycle is slower.

## Consequences

- Mini-App will hit a Python HTTP API; type sharing happens via generated client from OpenAPI, not via a shared language.
- Async-throughout requires async-aware libraries (asyncpg over psycopg2, httpx over requests).
- Single-process MVP can split into separate bot-worker and api-worker later without code change (both import the same handlers).
