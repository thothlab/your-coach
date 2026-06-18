# Task 04 — Groups & memberships

## Goal
Implement group creation, listing, and membership lifecycle (`pending → active → removed`). Covers all `groups/` spec scenarios.

## Scope
**In:** `Group` and `Membership` tables; `POST /groups`, `GET /groups`, `GET /groups/:id/members`, `DELETE /groups/:id/members/:athlete_id`; auto-activation on athlete's first authed call.
**Out:** invite endpoints (Task 03), sessions (Task 06).

## Subtasks
1. Migrate `Group` table (`id`, `trainer_id`, `name`, `type`, `created_at`).
2. Migrate `Membership` table (`group_id`, `athlete_id`, `status`, `joined_at`), composite PK.
3. Implement `POST /groups` (trainer-only) with validation: `type ∈ {group, personal}`, `name` non-empty.
4. Implement `GET /groups` returning trainer's groups with active member counts.
5. Implement `GET /groups/:id/members` returning each membership with athlete name.
6. Implement `DELETE /groups/:id/members/:athlete_id` (trainer-only): transition `active → removed`.
7. Implement post-auth hook in `POST /auth/telegram`: for athletes, flip the most recent `pending` membership to `active`.
8. Enforce visibility rule for athletes: any `GET` involving sessions/members of a group rejects if athlete has no `active` membership.

## Deliverables
- `Group`, `Membership` migrations
- 4 HTTP routes above
- Visibility middleware/helper for athlete-scoped queries

## Definition of Done
- [ ] Trainer can create both `group` and `personal` groups
- [ ] Athlete's first authed `/auth/telegram` flips their `pending` membership to `active`
- [ ] `DELETE` member → status `removed`; subsequent athlete `GET /sessions/:id` of that group returns `403`
- [ ] Visibility tests: no leak across trainers; athlete only sees their own active groups' data

## Tests
Tied to `specs/groups/spec.md` scenarios:
- "Trainer creates a group"
- "Trainer creates a personal slot"
- "Athlete first opens the Mini-App"
- "Trainer removes an athlete"
- "Removed athlete cannot read past session details"

## Dependencies
Task 02.
