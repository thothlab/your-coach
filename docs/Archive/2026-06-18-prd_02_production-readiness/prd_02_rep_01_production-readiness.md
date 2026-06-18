# prd_02_rep_01 — Planning report

## What was done

Decomposed "Production readiness" into 7 tasks across runtime, deployment, bot, and Mini-App. Three delta specs touch existing domains (`bot-ui`, `mini-app`) and seed a new `deployment` domain.

Key scope cuts confirmed in the PRD:
- No payments — still PRD-03 candidate
- No custom domain purchase — Fly's `*.fly.dev` is acceptable for first paying trainer
- No Sentry / external error reporting — stdout JSON logs only; PRD-03 candidate
- No horizontal scaling — single Fly machine; documented as out of scope

## Files produced

PRD package at `docs/PRDs/prd_02_production-readiness/`:

- `prd_02_scratch.md`
- `prd_02_production-readiness.md`
- `specs/bot-ui/spec.md` — MODIFIED `/invite` requirement
- `specs/mini-app/spec.md` — ADDED 5 requirements
- `specs/deployment/spec.md` — NEW domain, 6 requirements
- `prd_02_task_01_container-and-worker.md`
- `prd_02_task_02_fly-deploy.md`
- `prd_02_task_03_botfather-setup.md`
- `prd_02_task_04_invite-fsm.md`
- `prd_02_task_05_mini-app-router-and-forms.md`
- `prd_02_task_06_trainer-create-screens.md`
- `prd_02_task_07_trainer-schedule-and-broadcast.md`
- `prd_02_rep_01_production-readiness.md` — this file

Total: **13 files**.

## Affected domains

On archive of PRD-02, the following living specs will change:

- `docs/specs/bot-ui/spec.md` — `Requirement: /invite walks the trainer through group selection` replaced with the multi-group variant
- `docs/specs/mini-app/spec.md` — 5 new ADDED requirements appended
- `docs/specs/deployment/spec.md` — new file, 6 requirements seeded

## Deviations from input

Original input listed:
1. Real deploy with HTTPS + BotFather config
2. Notification worker as cron
3. Trainer Mini-App screens
4. Extended `/invite` FSM

All four are covered. Deviations:

- Worker runs **in-process** with `apscheduler` (not a separate cron container) — simpler operationally for one-machine MVP; flagged as a PRD-03 split candidate if outage isolation matters.
- Bot uses **webhook** in production (vs long-polling locally) — required by Fly's idle-and-stop machine model. ADR-06 records the choice.
- BotFather setup is a **manual one-time script** (not zero-touch automation). Token-bearing operations need a user-supplied secret; full automation would mean storing the BotFather session, which is not a path we should take.
- The `/invite` FSM is **stateless**: group_id + timestamp encoded in `callback_data` rather than aiogram FSM storage. Avoids RAM-bound state that doesn't survive restart.

## Recommended execution order

1. **Task 01** — Container + worker (foundation; everything else assumes the unified runtime)
2. **Task 04** — `/invite` FSM (backend-only, parallelizable with Mini-App work)
3. **Task 05** — Mini-App router + form primitives (unblocks Tasks 06 + 07)
4. **Task 06** — Trainer creation screens
5. **Task 07** — Session create + Broadcast composer
6. **Task 02** — Fly.io deploy config (can land any time after Task 01; benefits from being last so deploy ships a complete product)
7. **Task 03** — BotFather setup script (runs once after first successful Task 02 deploy)

A two-contributor split: backend (Tasks 01 → 04 → 02 → 03) and frontend (Tasks 05 → 06 → 07).

## Next step

**Task 01 — Container + in-process worker.** Largest single task; unblocks the rest. Deliverable highlights: Dockerfile, `serve` subcommand, `apscheduler`, `telegram_sender`, `/api/telegram/webhook`, `/readyz`, static asset mounting, JSON logging.

## Notes for archive

- The current `notifications/` living spec already references "the scheduler's hourly sweep" — PRD-02 implements that sweep; no behavioural spec change needed on `notifications/`.
- Archive will create `docs/specs/deployment/spec.md` for the first time.
- Mini-App initial bundle stays under 250 KB gz throughout — measured at each task's DoD.
