# bot-ui — delta for PRD-02

## MODIFIED Requirements

### Requirement: `/invite` walks the trainer through group selection
The system MUST reply to `/invite` with an inline keyboard listing the trainer's groups; selecting a group MUST return a fresh invite URL within 30 seconds wall-clock. With exactly one group the selection step MUST be skipped. With zero groups the bot MUST direct the trainer to the Mini-App's group-creation screen.

#### Scenario: Trainer has one group
- GIVEN a trainer who owns exactly one group `G`
- WHEN the trainer sends `/invite`
- THEN the bot skips selection and replies directly with a fresh invite URL for `G`

#### Scenario: Trainer has zero groups
- GIVEN a trainer who owns no groups
- WHEN the trainer sends `/invite`
- THEN the bot replies "Create a group first" with a button that opens the Mini-App to the group-creation screen

#### Scenario: Trainer has multiple groups — picker shown
- GIVEN a trainer who owns groups `G1`, `G2`, `G3`
- WHEN the trainer sends `/invite`
- THEN the bot replies with an inline keyboard containing exactly three buttons labelled `G1`, `G2`, `G3`
- AND each button's `callback_data` uniquely identifies the target group

#### Scenario: Trainer taps a group on the picker
- GIVEN the picker message described above is on screen
- WHEN the trainer taps a button for group `G2`
- THEN the bot edits the original message to show "Invite for G2: <URL>"
- AND a fresh `Invite` row exists with `group_id = G2.id` and `used_at IS NULL`
- AND wall-clock from `/invite` to the URL reply is ≤ 30 seconds

#### Scenario: Picker tap after expiration
- GIVEN a picker message older than 5 minutes
- WHEN the trainer taps a group button
- THEN the bot replies "selection expired — send /invite again" and no `Invite` row is created
