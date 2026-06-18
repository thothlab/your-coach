# Task 06 — Trainer creation screens (groups, exercises, workouts)

## Goal
Three creation forms that let the trainer go from empty workspace to having a workout template ready to attach to a session — all from inside the Mini-App.

## Scope
**In:** GroupCreate, ExerciseCreate, WorkoutTemplateCreate pages; list + entry-point buttons on trainer home / workouts page.
**Out:** edit / delete (defer); media uploads.

## Subtasks
1. **Group create page** (`/groups/new`): name input + type select; submit → `POST /api/groups`; on success navigate back to home with the new group at the top.
2. **Workouts page** (`/workouts`) listing existing templates with "New template" button.
3. **Exercise create page** (`/exercises/new`): name + unit (segmented control: reps / kg / seconds / meters). Submit → `POST /api/exercises`. Optionally allow adding multiple in a row.
4. **Workout template create page** (`/workouts/new`):
   - Name input
   - Item list (start with 1 item; +Add item button to append)
   - Each item: exercise picker (loaded from `GET /api/exercises`), sets, conditional fields per unit (reps, weight, seconds) per existing validator
   - Reorder via up/down buttons (no drag for MVP)
   - Submit → `POST /api/workouts`; surface server-side validation errors per item

## Deliverables
- `mini-app/src/pages/GroupCreate.tsx`
- `mini-app/src/pages/Workouts.tsx`
- `mini-app/src/pages/ExerciseCreate.tsx`
- `mini-app/src/pages/WorkoutTemplateCreate.tsx`
- `mini-app/src/api.ts` — UPDATE if any client method missing

## Definition of Done
- [ ] All three forms render without console errors
- [ ] Group create round-trip leaves the trainer on the home with the new group visible
- [ ] Exercise create round-trip leaves the trainer on `/exercises` with the new entry visible
- [ ] Template create with 2 items hits `POST /api/workouts` exactly once; new template visible on `/workouts`
- [ ] Invalid template (e.g. `kg` exercise without `target_weight`) surfaces server error next to the offending field
- [ ] Bundle ≤ 250 KB gz after these screens

## Tests
Tied to `specs/mini-app/spec.md`:
- "Trainer creates a group"
- "Server validation surfaced inline"
- "Trainer creates an exercise"
- "Trainer builds a workout template"

## Dependencies
Task 05.
