# Task 05 — Mini-App router + form primitives

## Goal
Introduce `@solidjs/router` (already a dep) configured in **memory mode** so navigation doesn't change `window.location` inside Telegram. Add a small set of reusable form primitives (Field, Input, Select, FormShell) the trainer-side screens build on.

## Scope
**In:** Router setup with named routes; layout shell with Telegram BackButton wiring; shared form primitives + base validation helper; replace the ad-hoc `openSessionId` signal in `App.tsx` with router-based navigation.
**Out:** real screens (Tasks 06 + 07); animations.

## Subtasks
1. Convert `App.tsx` to use `Router` with `Route` definitions: `/`, `/groups/new`, `/exercises`, `/exercises/new`, `/workouts`, `/workouts/new`, `/sessions/new`, `/broadcast`, `/sessions/:id`.
2. Use `memoryIntegration()` from `@solidjs/router` so URL stays constant.
3. Wire Telegram WebApp `BackButton`: visible on non-root routes; tap calls `navigator(-1)` to go back without URL change.
4. Implement `src/ui/Field.tsx`, `src/ui/Input.tsx`, `src/ui/Select.tsx`, `src/ui/FormShell.tsx`, `src/ui/SubmitBar.tsx`, `src/ui/Spinner.tsx`.
5. Implement `src/ui/api-error.ts` — surfaces 4xx detail strings on the right field, falls back to top-of-form banner.

## Deliverables
- `mini-app/src/App.tsx` — UPDATE
- `mini-app/src/routes.tsx` — route table
- `mini-app/src/ui/*.tsx` — form primitives (≤ 6 files)
- `mini-app/src/lib/telegram.ts` — UPDATE: expose `setBackButton(visible: boolean, onTap: () => void)`

## Definition of Done
- [ ] Bundle remains ≤ 250 KB gz after router + primitives addition
- [ ] Trainer home → tap "Create group" → URL unchanged (verified via window.location snapshot in a vitest)
- [ ] Back button in Telegram appears on `/groups/new` and dismisses the form
- [ ] Server validation errors land next to the field per `api-error.ts`

## Tests
Tied to `specs/mini-app/spec.md`:
- "Mini-App routes use in-app navigation without URL changes" (vitest with jsdom + `location.href` snapshot)
- Bundle-size budget remains green

## Dependencies
None within PRD-02. Builds on PRD-01 Mini-App.
