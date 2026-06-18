# Task 02 — Fly.io deploy pipeline

## Goal
Produce all the config so that `git push origin main` deploys the Task 01 image to Fly.io after CI passes. User does one-time `fly auth login && fly launch` manually; subsequent deploys are non-interactive.

## Scope
**In:** `fly.toml`, GitHub Action `deploy` job, `.env.production.example`, post-deploy smoke check, README runbook for first-time setup, Decision docs 05 (hosting) and 06 (delivery mode).
**Out:** custom domain purchase, Sentry, scaling.

## Subtasks
1. Write `fly.toml` with: app name placeholder, internal port 8000, health check on `/healthz`, auto-stop disabled (so scheduler keeps running).
2. Document Fly Postgres attach (`fly pg create` + `fly pg attach`) in `docs/decisions/05-hosting.md`.
3. Write `docs/decisions/06-delivery-mode.md`: webhook in prod, polling in dev, with the rationale.
4. Extend `.github/workflows/ci.yml` with a `deploy` job that:
   - depends on `backend` + `mini-app` jobs being green
   - runs only on push to `main` (not PR)
   - uses `superfly/flyctl-actions/setup-flyctl@master`
   - runs `flyctl deploy --remote-only` with `FLY_API_TOKEN` from repo secrets
   - hits `https://${{ vars.FLY_APP_NAME }}.fly.dev/healthz` after deploy, fails if non-200
5. `.env.production.example` listing every required env var (no values).
6. `README` section: "First-time deploy" — exact commands the user runs once.

## Deliverables
- `fly.toml`
- `.env.production.example`
- `.github/workflows/ci.yml` — UPDATE with deploy job
- `docs/decisions/05-hosting.md`
- `docs/decisions/06-delivery-mode.md`
- `README.md` — UPDATE with deploy runbook

## Definition of Done
- [ ] `fly.toml` syntax-validates with `flyctl config validate` (manual check documented)
- [ ] CI deploy job only runs on push to `main`, never on PR
- [ ] CI deploy job fails loudly if `FLY_API_TOKEN` secret is missing
- [ ] README runbook can be followed by a new developer with no prior Fly account
- [ ] Decision docs ADR-style: chosen / rejected / consequences

## Tests
Tied to `specs/deployment/spec.md`:
- "Service is reachable over public HTTPS after deploy" (verified live by first manual deploy)
- "Secrets are managed by the host, never committed" — `scripts/scan_for_secrets.py` grep regex in CI

## Dependencies
Task 01.
