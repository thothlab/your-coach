# groups — delta for PRD-01

## ADDED Requirements

### Requirement: Trainer can create group and personal training rosters
The system MUST let a trainer create groups of two types — `group` (multi-athlete classes) and `personal` (one-on-one) — and list active memberships.

#### Scenario: Trainer creates a group
- GIVEN an authenticated trainer
- WHEN the trainer submits `POST /groups` with `{name: "Monday strength", type: "group"}`
- THEN the API returns `201` with the new `Group` and `trainer_id = trainer.id`

#### Scenario: Trainer creates a personal slot
- GIVEN an authenticated trainer
- WHEN the trainer submits `POST /groups` with `{name: "Anna — personal", type: "personal"}`
- THEN the API returns `201` and the group accepts at most one active athlete

### Requirement: Membership lifecycle reflects athlete engagement
The system MUST transition `Membership.status` `pending → active` on the athlete's first authenticated Mini-App open after invite redemption, and MUST let the trainer transition `active → removed`.

#### Scenario: Athlete first opens the Mini-App
- GIVEN a `Membership(group_id=G, athlete_id=A, status=pending)`
- WHEN athlete `A` makes their first authenticated `GET /me` call
- THEN the system updates `Membership.status = active`

#### Scenario: Trainer removes an athlete
- GIVEN an `active` membership of athlete `A` in group `G` owned by trainer `T`
- WHEN trainer `T` submits `DELETE /groups/G/members/A`
- THEN the system updates `Membership.status = removed`
- AND athlete `A` no longer sees sessions of `G` in subsequent `GET /sessions` responses

### Requirement: Athlete visibility is limited to own groups
The system MUST restrict an athlete's view of sessions, broadcasts, and members to groups where the athlete has `Membership.status = active`.

#### Scenario: Removed athlete cannot read past session details
- GIVEN athlete `A` whose membership in `G` is now `removed`
- WHEN `A` calls `GET /sessions/:id` for a past session of `G`
- THEN the API responds `403 Forbidden`
