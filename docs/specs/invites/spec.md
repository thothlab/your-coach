# invites — living spec

## Requirements

### Requirement: Trainer can generate a single-use invite link for a group
The system MUST issue an invite that is bound to one group, expires after 7 days, and is redeemable exactly once.

#### Scenario: Trainer generates invite from bot
- GIVEN a trainer who owns at least one group
- WHEN the trainer sends `/invite` and selects the target group
- THEN the bot replies with a `https://t.me/<bot>?start=<token>` URL where `<token>` is URL-safe random ≥ 128 bits
- AND the system stores an `Invite` row with `expires_at = now + 7 days` and `used_at = NULL`

#### Scenario: Invite generation time budget
- GIVEN a trainer in a Telegram chat with the bot
- WHEN the trainer sends `/invite` and picks a group
- THEN the bot replies with the link in ≤ 30 seconds wall-clock from `/invite` to incoming message

### Requirement: Invite redemption joins the athlete to the group
The system MUST attach the redeeming user as an `athlete` to the invite's group on first redemption and MUST reject any further redemption attempts of the same token.

#### Scenario: Fresh athlete redeems valid invite
- GIVEN an unused, non-expired `Invite(token=K, group_id=G)`
- AND no `User` row exists for Telegram id `T`
- WHEN Telegram delivers `/start K` from user `T`
- THEN the system creates `User(telegram_id=T, role=athlete)`
- AND creates `Membership(group_id=G, athlete_id=T, status=pending)`
- AND sets `Invite.used_at = now`, `Invite.used_by_user_id = User.id`
- AND the bot replies with a welcome message linking to the Mini-App

#### Scenario: Reused token is rejected
- GIVEN an `Invite(token=K)` with `used_at IS NOT NULL`
- WHEN any user sends `/start K`
- THEN the bot replies "This invite has already been used" and no membership is created

#### Scenario: Expired token is rejected
- GIVEN an `Invite(token=K)` with `expires_at < now` and `used_at IS NULL`
- WHEN any user sends `/start K`
- THEN the bot replies "This invite has expired" and no membership is created

### Requirement: Personal-group invariant survives concurrent redemption
The system MUST guarantee that a `group.type = personal` has at most one membership with `status = active` at any time, even under concurrent invite redemptions.

#### Scenario: Two athletes redeem invites to the same personal group
- GIVEN a `personal` group with no active members
- AND two unused invites `K1` and `K2` both bound to that group
- WHEN two different users redeem `K1` and `K2` within the same second
- THEN exactly one redemption succeeds; the other is rejected with "Personal slot already taken"
