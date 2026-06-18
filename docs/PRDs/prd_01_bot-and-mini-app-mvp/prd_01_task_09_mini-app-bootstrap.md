# Task 09 — Mini-App bootstrap

## Goal
Ship the Mini-App shell with Telegram-initData auth, role-aware routing, and the bundle-size budget. Covers Mini-App spec requirements that are not screen-specific (auth, routing, bundle, perf).

## Scope
**In:** Mini-App framework boot (per Task 01 decision), initData auth handshake, `/me` fetch, role-routed home shell, theme integration, error boundaries, bundle-size guard.
**Out:** schedule / session / log / history screens (Task 10), trainer group-management screens beyond a placeholder.

## Subtasks
1. Implement the initData boot sequence: parse `window.Telegram.WebApp.initData`, send to `POST /auth/telegram`, store session token, then call `GET /me`. No other network calls until both return.
2. Implement role-routed shell: on `role=trainer`, mount trainer home (groups list + schedule tab placeholders); on `role=athlete`, mount athlete home (upcoming sessions placeholder).
3. Integrate Telegram theme: respect `themeParams`, react to `themeChanged`.
4. Add error boundary that surfaces a non-blank screen on any uncaught error and offers a "Reopen app" button.
5. Configure build to fail if initial JS+CSS gzipped > 250 KB (CI integration from Task 01).
6. Add Lighthouse-style local perf check: first interactive frame ≤ 2 s on simulated 4 Mbps / 100 ms RTT (manual or automated via Playwright/Lighthouse run in CI).

## Deliverables
- Mini-App app entry, router, auth client
- Trainer home shell (with placeholder content)
- Athlete home shell (with placeholder content)
- Error boundary
- CI bundle-size + perf checks active

## Definition of Done
- [ ] Cold boot: first network call is `POST /auth/telegram` (verified via network-capture test)
- [ ] No data calls before `GET /me` returns
- [ ] Trainer and athlete land on distinct home screens
- [ ] Theme params applied; switching Telegram theme updates UI
- [ ] CI fails if budget exceeded (red build on a forced violation test)
- [ ] First interactive frame ≤ 2 s in CI perf check

## Tests
Tied to `specs/mini-app/spec.md` scenarios:
- "Cold start handshake"
- "Trainer lands on trainer home"
- "Athlete lands on athlete home"
- "Bundle size budget"

## Dependencies
Tasks 01, 02.
