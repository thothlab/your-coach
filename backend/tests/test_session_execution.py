from datetime import UTC, datetime, timedelta

import pytest

from trainbeat.models import (
    AttendanceStatus,
    ExerciseUnit,
    GroupType,
    MembershipStatus,
    SessionStatus,
    UserRole,
)
from trainbeat.repositories import attendance as attendance_repo
from trainbeat.repositories import exercise as exercise_repo
from trainbeat.repositories import group as group_repo
from trainbeat.repositories import membership as membership_repo
from trainbeat.repositories import session as session_repo
from trainbeat.repositories import user as user_repo

from ._helpers import init_data_header


async def _make_world(db_session, *, scheduled_at, athlete_active=True):
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    athlete = await user_repo.create(
        db_session, telegram_id=2, name="A", role=UserRole.athlete
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    await membership_repo.create(
        db_session,
        group_id=group.id,
        athlete_id=athlete.id,
        status=MembershipStatus.active if athlete_active else MembershipStatus.pending,
    )
    row = await session_repo.create_one_off(
        db_session,
        group_id=group.id,
        workout_template_id=None,
        scheduled_at=scheduled_at,
        duration_min=60,
    )
    await attendance_repo.initialize_for_session(
        db_session, session_id=row.id, group_id=group.id
    )
    return coach, athlete, group, row


@pytest.mark.asyncio
async def test_athlete_confirms_via_mini_app(http_client, db_session) -> None:
    """Scenario: Athlete confirms via Mini-App."""
    _, _, _, row = await _make_world(
        db_session, scheduled_at=datetime.now(UTC) + timedelta(days=1)
    )

    response = await http_client.post(
        f"/api/sessions/{row.id}/attendance",
        json={"status": "confirmed"},
        headers=init_data_header(2),
    )
    assert response.status_code == 200
    att = await attendance_repo.get(db_session, session_id=row.id, athlete_id=2)
    await db_session.refresh(att)
    # athlete telegram_id=2; db user id may not be 2 but lookup by athlete_id from DB User
    user = await user_repo.get_by_telegram_id(db_session, 2)
    att = await attendance_repo.get(db_session, session_id=row.id, athlete_id=user.id)
    await db_session.refresh(att)
    assert att.status == AttendanceStatus.confirmed


@pytest.mark.asyncio
async def test_attendance_change_blocked_after_session_ends(http_client, db_session) -> None:
    """Scenario: Attendance change blocked after session ends."""
    _, _, _, row = await _make_world(
        db_session, scheduled_at=datetime.now(UTC) - timedelta(hours=2)
    )

    response = await http_client.post(
        f"/api/sessions/{row.id}/attendance",
        json={"status": "confirmed"},
        headers=init_data_header(2),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_trainer_marks_present(http_client, db_session) -> None:
    """Scenario: Trainer marks present."""
    _, athlete, _, row = await _make_world(
        db_session, scheduled_at=datetime.now(UTC) - timedelta(minutes=5)
    )
    att = await attendance_repo.get(db_session, session_id=row.id, athlete_id=athlete.id)
    await attendance_repo.set_status(db_session, att, AttendanceStatus.confirmed)

    response = await http_client.post(
        f"/api/sessions/{row.id}/attendance/{athlete.id}",
        json={"status": "present"},
        headers=init_data_header(1),
    )
    assert response.status_code == 200
    fresh = await attendance_repo.get(
        db_session, session_id=row.id, athlete_id=athlete.id
    )
    await db_session.refresh(fresh)
    assert fresh.status == AttendanceStatus.present


@pytest.mark.asyncio
async def test_marking_present_before_start_rejected(http_client, db_session) -> None:
    """Scenario: Marking present before start is rejected."""
    _, athlete, _, row = await _make_world(
        db_session, scheduled_at=datetime.now(UTC) + timedelta(hours=2)
    )

    response = await http_client.post(
        f"/api/sessions/{row.id}/attendance/{athlete.id}",
        json={"status": "present"},
        headers=init_data_header(1),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_athlete_logs_first_set(http_client, db_session) -> None:
    """Scenario: Athlete logs first set."""
    coach, athlete, _, row = await _make_world(
        db_session, scheduled_at=datetime.now(UTC) - timedelta(minutes=10)
    )
    att = await attendance_repo.get(db_session, session_id=row.id, athlete_id=athlete.id)
    await attendance_repo.set_status(db_session, att, AttendanceStatus.confirmed)
    ex = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Squat", unit=ExerciseUnit.kg
    )

    response = await http_client.post(
        f"/api/sessions/{row.id}/log",
        json={
            "exercise_id": ex.id,
            "set_index": 1,
            "actual_reps": 8,
            "actual_weight": 80,
        },
        headers=init_data_header(2),
    )
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_out_of_order_set_index_rejected(http_client, db_session) -> None:
    """Scenario: Out-of-order set index is rejected."""
    coach, athlete, _, row = await _make_world(
        db_session, scheduled_at=datetime.now(UTC) - timedelta(minutes=10)
    )
    att = await attendance_repo.get(db_session, session_id=row.id, athlete_id=athlete.id)
    await attendance_repo.set_status(db_session, att, AttendanceStatus.confirmed)
    ex = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Squat", unit=ExerciseUnit.kg
    )

    response = await http_client.post(
        f"/api/sessions/{row.id}/log",
        json={
            "exercise_id": ex.id,
            "set_index": 3,
            "actual_reps": 8,
            "actual_weight": 80,
        },
        headers=init_data_header(2),
    )
    assert response.status_code == 400
    assert "next expected set_index is 1" in response.json()["detail"]


@pytest.mark.asyncio
async def test_all_attendance_set_completes_session(http_client, db_session) -> None:
    """Scenario: All attendance set ⇒ completed."""
    _, athlete, _, row = await _make_world(
        db_session, scheduled_at=datetime.now(UTC) - timedelta(minutes=10)
    )

    response = await http_client.post(
        f"/api/sessions/{row.id}/attendance/{athlete.id}",
        json={"status": "present"},
        headers=init_data_header(1),
    )
    assert response.status_code == 200

    fresh = await session_repo.get(db_session, row.id)
    await db_session.refresh(fresh)
    assert fresh.status == SessionStatus.completed


@pytest.mark.asyncio
async def test_grace_window_elapses_auto_completes(db_session) -> None:
    """Scenario: Grace window elapses ⇒ completed."""
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
        scheduled_at=datetime.now(UTC) - timedelta(days=2),
        duration_min=60,
    )

    flipped = await session_repo.auto_complete_expired(db_session)
    assert flipped >= 1
    fresh = await session_repo.get(db_session, row.id)
    await db_session.refresh(fresh)
    assert fresh.status == SessionStatus.completed


@pytest.mark.asyncio
async def test_athlete_sees_only_own_log_rows(http_client, db_session) -> None:
    """Scenario: Athlete sees only own log rows."""
    coach, athlete, _, row = await _make_world(
        db_session, scheduled_at=datetime.now(UTC) - timedelta(minutes=10)
    )
    other = await user_repo.create(
        db_session, telegram_id=3, name="B", role=UserRole.athlete
    )
    await membership_repo.create(
        db_session, group_id=row.group_id, athlete_id=other.id, status=MembershipStatus.active
    )
    att1 = await attendance_repo.get(db_session, session_id=row.id, athlete_id=athlete.id)
    await attendance_repo.set_status(db_session, att1, AttendanceStatus.confirmed)
    # also initialize attendance for other (group had 1 active member when session created)
    from trainbeat.models import Attendance
    db_session.add(
        Attendance(
            session_id=row.id, athlete_id=other.id, status=AttendanceStatus.confirmed
        )
    )
    await db_session.commit()

    ex = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Squat", unit=ExerciseUnit.kg
    )

    await http_client.post(
        f"/api/sessions/{row.id}/log",
        json={"exercise_id": ex.id, "set_index": 1, "actual_reps": 5, "actual_weight": 40},
        headers=init_data_header(2),
    )
    await http_client.post(
        f"/api/sessions/{row.id}/log",
        json={"exercise_id": ex.id, "set_index": 1, "actual_reps": 6, "actual_weight": 50},
        headers=init_data_header(3),
    )

    own = await http_client.get(
        f"/api/sessions/{row.id}/log", headers=init_data_header(2)
    )
    assert own.status_code == 200
    body = own.json()
    assert len(body) == 1
    assert body[0]["athlete_id"] == athlete.id

    trainer = await http_client.get(
        f"/api/sessions/{row.id}/log", headers=init_data_header(1)
    )
    assert trainer.status_code == 200
    assert len(trainer.json()) == 2
