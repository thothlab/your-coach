# Decision 04 — Naming

**Date:** 2026-06-18
**Status:** Accepted (brand reserved; bot username pending BotFather confirmation)

## Decision

- **Product brand:** **TrainBeat**
- **Telegram bot username:** `@trainbeat_bot`
- **Mini-App display name:** TrainBeat
- **Tagline (working):** "Тренировки в ритме твоего тренера" / "Training in your trainer's rhythm"
- **Domain (to acquire later):** `trainbeat.app` (preferred), `trainbeat.fit` (fallback)

The OS-level working directory remains `your-coach/` for continuity; the published repo will be `trainbeat` when pushed to a remote.

## Rationale

- Short (9 chars), pronounceable in RU and EN.
- Rhythm/beat metaphor covers strength, cardio, and class formats — wider audience than fitness-vernacular alternatives (`SetReps`).
- Avoids the generic "Coach/Fit/Train" lexicon collisions on Telegram.
- Bot username available at time of decision (must be re-checked in BotFather at registration).

## Rejected candidates

| Candidate | Reason rejected |
|---|---|
| CoachLog | Sounded enterprise-y, less consumer-friendly. |
| TrenerHub | RU-only resonance; "Hub" suffix overused. |
| SetReps | Excludes yoga/Pilates trainers; too gym-specific. |
| PulseFit | "Pulse" already heavily used in fitness apps; collision risk. |

## Action required from the user

1. Open BotFather → `/newbot` → name "TrainBeat" → username `trainbeat_bot`.
2. Save the issued token into local `.env` (already gitignored). **Do not paste tokens into chat or commits.**
3. Configure Mini-App URL via `/setmenubutton` once a public dev tunnel exists.

## Consequences

- All user-visible copy, README, and Mini-App branding use "TrainBeat".
- Python package is `trainbeat` (`src/trainbeat/`).
- Backend service is identified as `trainbeat-api` in deploy manifests.
