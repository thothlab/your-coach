# prd_01_rep_01 — Planning report

## What was done
Decomposed `docs/idea.md` into PRD-01 (Bot + Mini-App MVP) with explicit scope cuts: payments, mobile/web apps, video, AI generation, and gym/multi-trainer mode are deferred to later PRDs. Wrote a delta-style spec set across 9 domains and 10 implementation tasks with dependencies that allow incremental delivery and CI-verifiable acceptance.

## Files produced

PRD package at `docs/PRDs/prd_01_bot-and-mini-app-mvp/`:

- `prd_01_scratch.md` — analysis scratchpad
- `prd_01_bot-and-mini-app-mvp.md` — PRD (Objective, Non-objectives, Data model, API list, Validation & state transitions, Risks & mitigations, Acceptance criteria)
- `specs/identity/spec.md`
- `specs/invites/spec.md`
- `specs/groups/spec.md`
- `specs/workouts/spec.md`
- `specs/scheduling/spec.md`
- `specs/sessions/spec.md`
- `specs/notifications/spec.md`
- `specs/bot-ui/spec.md`
- `specs/mini-app/spec.md`
- `prd_01_task_01_bootstrap.md`
- `prd_01_task_02_identity-and-auth.md`
- `prd_01_task_03_invites.md`
- `prd_01_task_04_groups.md`
- `prd_01_task_05_workouts.md`
- `prd_01_task_06_scheduling.md`
- `prd_01_task_07_session-execution.md`
- `prd_01_task_08_notifications.md`
- `prd_01_task_09_mini-app-bootstrap.md`
- `prd_01_task_10_mini-app-screens.md`
- `prd_01_rep_01_bot-and-mini-app-mvp.md` — this file

Total: **21 files**.

## Affected domains
On archive of PRD-01, every delta spec will seed the first version of its living counterpart under `docs/specs/<domain>/spec.md`. Since no living specs exist yet, every delta is `ADDED` — no `MODIFIED` or `REMOVED` blocks.

Living specs that will be created on archive:
- `docs/specs/identity/spec.md`
- `docs/specs/invites/spec.md`
- `docs/specs/groups/spec.md`
- `docs/specs/workouts/spec.md`
- `docs/specs/scheduling/spec.md`
- `docs/specs/sessions/spec.md`
- `docs/specs/notifications/spec.md`
- `docs/specs/bot-ui/spec.md`
- `docs/specs/mini-app/spec.md`

## Deviations from input
`docs/idea.md` asks for several things outside a single MVP delivery, intentionally not included in PRD-01:

| Asked in `idea.md` | Where it landed |
|---|---|
| Market analysis | Surfaced as Task 01 sub-decisions (stack/storage/Mini-App) but **no market survey was performed** — recommend a separate research PRD if a competitive scan is needed. |
| Bot and Mini-App naming | Punted to Task 01 naming sub-task; "your-coach" used as placeholder. |
| Subscriptions and payments | **Excluded.** Candidate PRD-02. |
| Full server + mobile app + website | **Excluded.** Mini-App covers the MVP UX inside Telegram. Native apps and standalone web are candidate PRD-03+. |
| Invitations | Included (Task 03). |

PRD-01 also introduces decisions not asked for in `idea.md`:
- Personal-group "1 active athlete" invariant + concurrency guard
- 5/day/group broadcast rate limit (anti-spam)
- 250 KB gz bundle budget enforced in CI
- 24h initData freshness check (security guardrail)

## Recommended execution order
File numbering is artifact id, not execution order. By the `Dependencies` sections, the topologically sound order is:

1. Task 01 — Bootstrap
2. Task 02 — Identity & auth
3. Task 04 — Groups & memberships (before invites, because `/invite` needs a group to bind to)
4. Task 03 — Invites
5. Task 05 — Exercises & workout templates
6. Task 06 — Scheduling
7. Task 07 — Session execution
8. Task 08 — Notifications & broadcasts
9. Task 09 — Mini-App bootstrap (can run in parallel with backend Tasks 03-08 after Task 02)
10. Task 10 — Mini-App screens (last; depends on all backend tasks)

Tasks 09 and the backend chain can be parallelised by two contributors once Task 02 is done.

## Next step
**Task 01 — Bootstrap.** Specifically the four decision documents under `docs/decisions/` and the bot username reservation in BotFather. Until those land, every subsequent task is blocked on stack/naming.

## Notes for archive
- This PRD seeds the living-spec tree; the archive step (Step 8 of the `/prd` skill) will create `docs/specs/<domain>/spec.md` files from the `ADDED Requirements` blocks of each delta.
- Project is not yet a git repository, so the planning commit (Step 7) was skipped. Recommend `git init` before starting Task 01 so subsequent task DoD checklists can be tracked through commits.
