from datetime import UTC, datetime, timedelta

import pytest

from trainbeat.models import GroupType, MembershipStatus, UserRole
from trainbeat.repositories import group as group_repo
from trainbeat.repositories import membership as membership_repo
from trainbeat.repositories import session as session_repo
from trainbeat.repositories import user as user_repo

from ._helpers import init_data_header


@pytest.mark.asyncio
async def test_trainer_schedules_one_off_session(http_client, db_session) -> None:
    """Scenario: Trainer schedules a one-off session."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    when = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    response = await http_client.post(
        "/api/sessions",
        json={"group_id": group.id, "scheduled_at": when, "duration_min": 60},
        headers=init_data_header(1),
    )

    assert response.status_code == 201, response.text
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["status"] == "scheduled"
    assert rows[0]["recurrence_rule"] is None


@pytest.mark.asyncio
async def test_trainer_schedules_weekly_recurring(http_client, db_session) -> None:
    """Scenario: Trainer schedules a weekly-recurring session."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    start = datetime.now(UTC) + timedelta(days=1)

    response = await http_client.post(
        "/api/sessions",
        json={
            "group_id": group.id,
            "scheduled_at": start.isoformat(),
            "duration_min": 60,
            "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO",
        },
        headers=init_data_header(1),
    )

    assert response.status_code == 201
    rows = response.json()
    assert len(rows) >= 4
    for row in rows:
        assert row["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=MO"


@pytest.mark.asyncio
async def test_past_scheduled_at_rejected(http_client, db_session) -> None:
    """Scenario: Past-dated session is rejected."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()

    response = await http_client.post(
        "/api/sessions",
        json={"group_id": group.id, "scheduled_at": past, "duration_min": 60},
        headers=init_data_header(1),
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cancel_scheduled_session(http_client, db_session) -> None:
    """Scenario: Cancel scheduled session."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    row = await session_repo.create_one_off(
        db_session,
        group_id=group.id,
        workout_template_id=None,
        scheduled_at=datetime.now(UTC) + timedelta(days=3),
        duration_min=60,
    )

    response = await http_client.post(
        f"/api/sessions/{row.id}/cancel", headers=init_data_header(1)
    )
    assert response.status_code == 200

    fresh = await session_repo.get(db_session, row.id)
    await db_session.refresh(fresh)
    assert fresh.status.value == "cancelled"


@pytest.mark.asyncio
async def test_cancel_completed_session_conflicts(http_client, db_session) -> None:
    """Scenario: Cancel rejected after completion."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    row = await session_repo.create_one_off(
        db_session,
        group_id=group.id,
        workout_template_id=None,
        scheduled_at=datetime.now(UTC) + timedelta(days=3),
        duration_min=60,
    )
    from trainbeat.models import SessionStatus

    row.status = SessionStatus.completed
    await db_session.commit()

    response = await http_client.post(
        f"/api/sessions/{row.id}/cancel", headers=init_data_header(1)
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_athlete_calendar_scoped_to_active_groups(http_client, db_session) -> None:
    """Scenario: Athlete calendar view is scoped."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    athlete = await user_repo.create(
        db_session, telegram_id=2, name="A", role=UserRole.athlete
    )
    g_active = await group_repo.create(
        db_session, trainer_id=coach.id, name="Active", type=GroupType.group
    )
    g_other = await group_repo.create(
        db_session, trainer_id=coach.id, name="Other", type=GroupType.group
    )
    await membership_repo.create(
        db_session, group_id=g_active.id, athlete_id=athlete.id, status=MembershipStatus.active
    )
    await membership_repo.create(
        db_session, group_id=g_other.id, athlete_id=athlete.id, status=MembershipStatus.removed
    )
    await session_repo.create_one_off(
        db_session, group_id=g_active.id, workout_template_id=None,
        scheduled_at=datetime.now(UTC) + timedelta(days=1), duration_min=60,
    )
    await session_repo.create_one_off(
        db_session, group_id=g_other.id, workout_template_id=None,
        scheduled_at=datetime.now(UTC) + timedelta(days=1), duration_min=60,
    )

    response = await http_client.get(
        "/api/sessions",
        params={
            "from": datetime.now(UTC).isoformat(),
            "to": (datetime.now(UTC) + timedelta(days=14)).isoformat(),
        },
        headers=init_data_header(2),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["group_id"] == g_active.id


def test_rrule_expansion_produces_occurrences_in_window() -> None:
    start = datetime(2026, 6, 22, 19, 0, tzinfo=UTC)  # Monday
    moments = session_repo.expand_rrule("FREQ=WEEKLY;BYDAY=MO", dtstart=start)
    assert len(moments) >= 8  # ~60/7 = 8-9 Mondays
    assert moments[0] == start
    for a, b in zip(moments, moments[1:], strict=False):
        assert (b - a) == timedelta(days=7)
