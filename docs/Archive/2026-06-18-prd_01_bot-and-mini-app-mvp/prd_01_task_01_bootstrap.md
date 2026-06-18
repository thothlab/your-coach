# Task 01 — Bootstrap

## Goal
Land an empty-but-runnable repo with a documented stack choice, reserved Telegram identifiers, and a CI pipeline that runs lint + tests on every push. After this task, every subsequent task can `git pull && make dev` and have a working environment.

## Scope
**In:** stack/storage/Mini-App framework decisions, repo layout, Telegram bot username reservation, Mini-App brand name, dev environment (`make dev`), CI (lint + unit tests + build-size budget), `.env.example`.
**Out:** any business logic, any DB schema, any deployed environment.

## Subtasks
1. Compare candidate stacks (Python+aiogram, Node+grammY, Go+telego) on developer velocity, async story, and Mini-App API integration; record decision in `docs/decisions/01-stack.md`.
2. Pick storage (Postgres vs SQLite-for-MVP) and record in `docs/decisions/02-storage.md`.
3. Pick Mini-App framework (React+Vite vs SolidJS vs Svelte) optimised for the 250 KB gz budget; record in `docs/decisions/03-mini-app-stack.md`.
4. Naming sub-task: pick a final bot username, reserve it via BotFather, pick a Mini-App brand; record in `docs/decisions/04-naming.md`. Replace "your-coach" placeholder across the repo.
5. Scaffold backend project (entry point, config loader from `.env`, healthcheck route, dependency manifest).
6. Scaffold Mini-App project (entry point, build config, `index.html` shell).
7. Add `Makefile` targets: `dev`, `test`, `lint`, `build`.
8. Set up GitHub Actions: lint, unit tests, Mini-App build, bundle-size check (fail if gzipped initial > 250 KB).
9. Write top-level `README.md` with one-screen setup instructions.

## Deliverables
- `docs/decisions/01..04*.md` (4 files)
- Backend project skeleton, runnable via `make dev`
- Mini-App project skeleton, runnable via `make dev`
- `Makefile`, `.env.example`, `.github/workflows/ci.yml`
- Top-level `README.md`

## Definition of Done
- [ ] Decision docs exist with chosen option + rejected options + one-line rationale each
- [ ] Bot username is reserved in BotFather; token stored only in `.env` (not committed)
- [ ] `make dev` launches backend and Mini-App locally on a clean machine
- [ ] `make test` and `make lint` pass on an empty/sample test
- [ ] CI green on a sample PR
- [ ] CI fails when initial Mini-App bundle exceeds 250 KB gz (verified by temporarily importing a heavy lib)

## Tests
- CI workflow execution proves: lint, unit, build, bundle-size budget.
- Manual: clone repo on fresh machine, run `make dev`, hit `/healthz` on backend, open Mini-App URL — no errors.

## Dependencies
None.
