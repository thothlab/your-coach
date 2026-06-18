# Task 07 — Trainer Session create + Broadcast composer

## Goal
Close the trainer's authoring loop: schedule a session and send broadcasts. Together with Task 06, the trainer never needs to touch curl.

## Scope
**In:** SessionCreate page (one-off + weekly recurring), BroadcastCompose page, integrations from trainer home.
**Out:** Bulk session edit, broadcast scheduling for later.

## Subtasks
1. **Session create page** (`/sessions/new`):
   - Group picker (from `GET /api/groups`)
   - Workout template picker (optional; from `GET /api/workouts`)
   - Datetime input (browser-native `datetime-local`)
   - Duration input (minutes)
   - "Weekly recurring" toggle → revealed weekday multi-select (Mon..Sun); on submit serialize to `FREQ=WEEKLY;BYDAY=<picked>`
   - Submit → `POST /api/sessions`; show count of created occurrences; navigate back to home
2. **Broadcast page** (`/broadcast`):
   - Group picker
   - Multi-line text input
   - Show character count
   - Submit → `POST /api/groups/:id/broadcast`
   - On `202` → toast "Sent to N members" and clear text
   - On `429` → inline "Rate limit reached — try again later" without clearing text
3. Add "Create session" + "Broadcast" buttons on trainer home.

## Deliverables
- `mini-app/src/pages/SessionCreate.tsx`
- `mini-app/src/pages/BroadcastCompose.tsx`
- `mini-app/src/pages/TrainerHome.tsx` — UPDATE: new entry buttons
- `mini-app/src/api.ts` — UPDATE: `createSession`, `sendBroadcast` methods if missing

## Definition of Done
- [ ] One-off session round-trip: trainer submits future datetime → home shows new entry
- [ ] Weekly recurring with Mon+Wed → home shows ≥ 4 occurrences in the next 14 days
- [ ] Past datetime → server rejects with 400; surfaced inline near datetime field
- [ ] Broadcast success shows recipient count
- [ ] Broadcast 6th in 24h → "rate limit" inline message, no crash, text preserved
- [ ] Bundle ≤ 250 KB gz with all screens (Tasks 05 + 06 + 07)

## Tests
Tied to `specs/mini-app/spec.md`:
- "Trainer creates one-off session"
- "Trainer creates weekly-recurring session"
- "Trainer sends broadcast"
- "Broadcast hits rate limit"

## Dependencies
Task 05, Task 06.
