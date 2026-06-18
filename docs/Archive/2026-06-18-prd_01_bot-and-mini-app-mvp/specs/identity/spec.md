# identity — delta for PRD-01

## ADDED Requirements

### Requirement: User identity is keyed by Telegram user id
The system MUST identify every user by their Telegram `user.id` from the Telegram Bot API. Once created, a `User.role` MUST NOT change.

#### Scenario: First message creates a trainer
- GIVEN no `User` row exists for Telegram id `T`
- WHEN Telegram delivers `/start` from user `T` with no payload
- THEN the system creates `User(telegram_id=T, role=trainer, name=<Telegram display name>)` and replies with a trainer onboarding message

#### Scenario: Second user without invite is treated as athlete-pending
- GIVEN at least one trainer exists AND no `User` row exists for Telegram id `T`
- WHEN Telegram delivers `/start` from user `T` with no payload
- THEN the system replies "Ask your trainer for an invite link" and does NOT create a `User` row

### Requirement: Onboarding completes within two minutes for a typical trainer
The system SHOULD enable a first-time trainer to reach the Mini-App home screen in ≤ 2 minutes of wall-clock time from sending `/start`.

#### Scenario: Trainer onboarding stopwatch
- GIVEN a fresh Telegram account never seen by the bot
- WHEN the user sends `/start`, taps "Open app", and lands on the Mini-App home
- THEN total elapsed time is ≤ 120 seconds (measured server-side from first webhook to first `/me` response)

### Requirement: Mini-App requests are authorized by validated Telegram initData
The system MUST validate the Telegram WebApp `initData` HMAC on every Mini-App HTTP request and MUST reject `initData` older than 24 hours.

#### Scenario: Tampered initData is rejected
- GIVEN a Mini-App request with `initData` whose `hash` does not match HMAC-SHA256 over the sorted parameters using the bot token
- WHEN the API receives the request
- THEN the API responds `401 Unauthorized` and the request has no side effects

#### Scenario: Stale initData is rejected
- GIVEN a Mini-App request with `initData.auth_date` older than 24 hours
- WHEN the API receives the request
- THEN the API responds `401 Unauthorized`
