# bot-ui — delta for PRD-01

## ADDED Requirements

### Requirement: Bot exposes a minimal command surface
The system MUST handle the commands `/start`, `/invite`, and `/app`, and MUST advertise them via Telegram Bot API `setMyCommands` so the Telegram client shows them in the suggestion menu.

#### Scenario: Command menu reflects supported commands
- GIVEN a fresh bot deployment
- WHEN a Telegram client requests the command menu
- THEN the menu lists `/start`, `/invite`, `/app` with concise descriptions

### Requirement: `/start` deep links handle both onboarding paths
The system MUST treat `/start` with no payload as trainer onboarding (subject to first-user rule from `identity`), and `/start <token>` as athlete onboarding via invite redemption.

#### Scenario: Trainer enters bot directly
- GIVEN the bot has no users yet
- WHEN any user sends `/start`
- THEN the bot replies with trainer onboarding text and an "Open app" button

#### Scenario: Athlete follows invite link
- GIVEN a valid unused invite token `K`
- WHEN any user opens `https://t.me/<bot>?start=K`
- THEN Telegram delivers `/start K` and the bot replies with athlete welcome text and an "Open app" button

### Requirement: `/app` produces a Mini-App launch button
The system MUST reply to `/app` with a message containing one inline button whose `web_app.url` opens the Mini-App.

#### Scenario: Trainer opens Mini-App
- GIVEN an authenticated trainer
- WHEN the trainer sends `/app` and taps the inline button
- THEN the Telegram client opens the Mini-App and `initData` is available to the Mini-App JavaScript

### Requirement: `/invite` walks the trainer through group selection
The system MUST reply to `/invite` with an inline keyboard listing the trainer's groups; selecting a group MUST return a fresh invite URL within 30 seconds wall-clock.

#### Scenario: Trainer has one group
- GIVEN a trainer who owns exactly one group `G`
- WHEN the trainer sends `/invite`
- THEN the bot skips selection and replies directly with a fresh invite URL for `G`

#### Scenario: Trainer has zero groups
- GIVEN a trainer who owns no groups
- WHEN the trainer sends `/invite`
- THEN the bot replies "Create a group first" with a button that opens the Mini-App to the group-creation screen
