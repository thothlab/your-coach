# workouts — living spec

## Requirements

### Requirement: Trainer maintains a per-trainer exercise catalog
The system MUST let a trainer create exercises with a fixed unit (`reps`, `seconds`, `meters`, or `kg`) and list them for reuse across templates.

#### Scenario: Trainer creates an exercise
- GIVEN an authenticated trainer
- WHEN the trainer submits `POST /exercises` with `{name: "Back squat", unit: "kg"}`
- THEN the API returns `201` with the new `Exercise` scoped to `trainer_id = trainer.id`

#### Scenario: Athlete cannot create or read trainer-scoped exercises
- GIVEN an authenticated athlete
- WHEN the athlete calls `GET /exercises` or `POST /exercises`
- THEN the API responds `403 Forbidden`

### Requirement: Trainer assembles workout templates from exercises
The system MUST let a trainer compose a `WorkoutTemplate` from an ordered list of items where each item references one exercise and carries set/target metadata.

#### Scenario: Trainer creates a template
- GIVEN exercises `E1` (`unit=kg`) and `E2` (`unit=reps`) owned by the trainer
- WHEN the trainer submits `POST /workouts` with `{name: "Leg day", items: [{exercise_id: E1, sets: 4, target_reps: 8, target_weight: 80}, {exercise_id: E2, sets: 3, target_reps: 15}]}`
- THEN the API returns `201` with the template and items preserved in the submitted order

#### Scenario: Template referencing another trainer's exercise is rejected
- GIVEN trainer `T1` and an exercise `E_other` owned by trainer `T2`
- WHEN `T1` submits a template with `items: [{exercise_id: E_other, ...}]`
- THEN the API responds `400 Bad Request` and no template is created

### Requirement: Template targets match the exercise unit
The system MUST reject template items whose target fields are inconsistent with the referenced exercise's `unit`.

#### Scenario: Wrong target for unit
- GIVEN an exercise with `unit=seconds`
- WHEN a template item carries `target_weight` but no `target_seconds`
- THEN the API responds `400 Bad Request` with an explanation referencing the unit
