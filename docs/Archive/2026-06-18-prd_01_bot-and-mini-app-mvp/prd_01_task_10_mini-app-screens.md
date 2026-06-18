# Task 10 — Mini-App screens

## Goal
Ship the user-facing screens that drive the MVP value: schedule, session detail with logging, athlete history (trainer view). Covers screen-specific Mini-App spec scenarios.

## Scope
**In:** Trainer screens — Groups list/create, Workouts list/create, Schedule (with create), Session detail (attendance + read logs), Athlete profile/history. Athlete screens — Schedule (upcoming), Session detail (confirm attendance, log results in three taps), own history.
**Out:** payments, broadcast composer beyond a minimal text input, multi-language UI beyond RU+EN copy strings.

## Subtasks
1. Schedule view (trainer + athlete):
   - 14-day rolling window via `GET /sessions?from&to` with expanded RRULE occurrences.
   - Sort by `scheduled_at`; group by date.
2. Session detail (athlete):
   - Show workout template (exercises with target sets/reps/weight/seconds).
   - "Confirm" / "Decline" buttons → `POST /sessions/:id/attendance`.
   - Exercise tap → set-entry sheet with the three-tap log path.
3. Session detail (trainer):
   - Roster with per-athlete `present|absent` controls (enabled after `scheduled_at`).
   - Read-only view of every athlete's logs.
4. Groups screen (trainer):
   - List groups with active counts.
   - Create group form (`name`, `type`).
   - Drill-in: members list with remove action, "Generate invite" button.
5. Workouts screen (trainer):
   - List templates.
   - Create-template form: pick exercises in order, fill targets per unit (validator inline).
6. Athlete history:
   - Trainer view: profile + reverse-chronological past sessions, expandable to logs.
   - Athlete view: own past sessions + logs.
7. Implement broadcast composer (trainer): pick group, type text, send.

## Deliverables
- All screens above wired to existing API
- Reusable form / list / sheet primitives
- RU + EN copy bundles

## Definition of Done
- [ ] Schedule view shows expanded recurring sessions over 14 days
- [ ] Athlete can log a set in exactly three taps (open exercise → enter values → save)
- [ ] Logged set appears in the list without a full reload
- [ ] Trainer mark-present is disabled before `scheduled_at`, enabled after
- [ ] Trainer can open an athlete's history and see past sessions with logs
- [ ] Trainer can send a broadcast and see member-count confirmation
- [ ] Bundle remains within the 250 KB gz budget

## Tests
Tied to `specs/mini-app/spec.md` and `specs/sessions/spec.md`:
- "Athlete can log a workout result in three taps" (E2E: count taps via Playwright)
- "Schedule view shows expanded recurring occurrences" (E2E with seeded RRULE session)
- "Trainer can review athlete history from Mini-App"
- Plus PRD-level acceptance criterion #9 (end-to-end happy path) executed as a single Playwright scenario.

## Dependencies
Tasks 03, 04, 05, 06, 07, 08, 09.
