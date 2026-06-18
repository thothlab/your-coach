# Decision 02 — Storage

**Date:** 2026-06-18
**Status:** Accepted

## Decision

Primary store is **PostgreSQL 16** from day one, accessed via **SQLAlchemy 2 async + asyncpg**, with schema migrations managed by **Alembic**.

## Rationale

- PRD-01 contains concurrency-sensitive invariants (personal-group "1 active athlete" guard, idempotent reminder delivery) that benefit from PG's strong transactional semantics and `INSERT … WHERE NOT EXISTS` patterns.
- RRULE-expanded scheduling and reminder windows are easier with PG's timestamp arithmetic, `generate_series`, and partial indexes.
- JSONB available for the `Notification.payload` and any future flexible fields.
- Avoids a forced SQLite → PG migration when concurrency or hosted-deploy needs hit.

## Rejected

- **SQLite for MVP, PG later** — would save ~30 min of dev setup, but the concurrency guard test (two athletes redeeming an invite to the same personal group simultaneously) is unreliable on SQLite without WAL+timeouts gymnastics; also, every future migration would require porting SQL dialect differences.

## Consequences

- Developers run PG locally via `docker compose up db` (added in scaffold).
- CI uses a service container for PG.
- Production hosting must include a PG instance; cheapest options are managed (Neon, Supabase, Render).
