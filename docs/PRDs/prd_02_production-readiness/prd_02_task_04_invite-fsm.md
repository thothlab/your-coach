# Task 04 — Extended `/invite` with group picker

## Goal
Cover the multi-group case for `/invite` per `specs/bot-ui/spec.md` MODIFIED requirement. Single-group and zero-group flows from PRD-01 keep working unchanged.

## Scope
**In:** Inline-keyboard picker on `/invite`, callback handler for group selection with 5-minute expiry, refactor `bot.py` to extract pure logic.
**Out:** persistent FSM storage; we encode group_id directly in `callback_data` to avoid storing transient state.

## Subtasks
1. Extract `list_trainer_groups_for_invite(session, trainer_id) -> list[Group]` helper (already exists via `group_repo.list_for_trainer`).
2. In `handle_invite` (new): if 0 groups → existing redirect; if 1 → existing auto-create; if ≥ 2 → reply with inline keyboard, button labels = group names, `callback_data = "invite:<group_id>:<unix_ts>"`.
3. Callback handler `handle_invite_pick`: parse `callback_data`, verify timestamp within 5 minutes, verify caller still owns the group, generate invite via `invite_repo.create`, edit original message to show URL.
4. Tests: pure-function variant `prepare_invite_response(session, trainer_id) -> Variant` covers branching; integration test for callback parse + invite creation.

## Deliverables
- `backend/src/trainbeat/bot.py` — UPDATE with `/invite` handler + callback
- Tests in `backend/tests/test_invite_fsm.py`

## Definition of Done
- [ ] Trainer with 1 group → URL reply, no picker
- [ ] Trainer with 0 groups → redirect reply
- [ ] Trainer with 3 groups → 3-button inline keyboard, each with distinct group label
- [ ] Tap valid button within 5 min → invite created, message edited with URL
- [ ] Tap after 5 min → "selection expired" reply, no Invite row created
- [ ] Tap a button referencing a group the trainer no longer owns → graceful error

## Tests
Tied to `specs/bot-ui/spec.md`:
- "Trainer has one group"
- "Trainer has zero groups"
- "Trainer has multiple groups — picker shown"
- "Trainer taps a group on the picker"
- "Picker tap after expiration"

## Dependencies
Task 01 (webhook endpoint; locally polling still works for tests).
