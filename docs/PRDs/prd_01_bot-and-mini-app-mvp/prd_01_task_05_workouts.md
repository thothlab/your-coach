# Task 05 — Exercises & workout templates

## Goal
Implement the trainer's exercise catalog and workout templates. Covers all `workouts/` spec scenarios.

## Scope
**In:** `Exercise` and `WorkoutTemplate` tables; `GET/POST /exercises`, `GET/POST /workouts`; cross-trainer ownership checks; unit/target consistency validator.
**Out:** assigning a template to a session (Task 06), logging results (Task 07).

## Subtasks
1. Migrate `Exercise` (`id`, `trainer_id`, `name`, `unit ∈ {reps, seconds, meters, kg}`).
2. Migrate `WorkoutTemplate` (`id`, `trainer_id`, `name`) and `workout_template_items` (`template_id`, `position`, `exercise_id`, `sets`, `target_reps`, `target_weight`, `target_seconds`) — ordered by `position`.
3. Implement `POST /exercises` (trainer-only) with unit validation.
4. Implement `GET /exercises` returning trainer-scoped catalog.
5. Implement `POST /workouts`: validate every `exercise_id` is owned by the caller; validate unit-target consistency per the rule below; persist items preserving `position`.
6. Implement `GET /workouts` returning trainer's templates with items.

## Unit-target consistency rule
- `unit=reps` → `target_reps REQUIRED`, `target_weight` allowed, `target_seconds FORBIDDEN`
- `unit=kg` → `target_reps REQUIRED`, `target_weight REQUIRED`, `target_seconds FORBIDDEN`
- `unit=seconds` → `target_seconds REQUIRED`, others forbidden
- `unit=meters` → `target_reps REQUIRED` (interpreted as distance count) or `target_seconds REQUIRED`; documented in API reference

## Deliverables
- Migrations
- 4 HTTP routes
- Unit-consistency validator with unit tests

## Definition of Done
- [ ] Trainer creates exercises and reads them back ordered by `name`
- [ ] Athlete role hits `403` on both exercise and workout endpoints
- [ ] Template creation rejects items referencing another trainer's exercises (`400`)
- [ ] Template creation rejects items with target/unit mismatch (`400`)
- [ ] Template items are returned in submitted order

## Tests
Tied to `specs/workouts/spec.md` scenarios:
- "Trainer creates an exercise"
- "Athlete cannot create or read trainer-scoped exercises"
- "Trainer creates a template"
- "Template referencing another trainer's exercise is rejected"
- "Wrong target for unit"

## Dependencies
Task 02.
