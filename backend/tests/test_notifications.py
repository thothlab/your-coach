from datetime import UTC, datetime, timedelta

import pytest

from trainbeat.models import GroupType, MembershipStatus, NotificationStatus, UserRole
from trainbeat.repositories import group as group_repo
from trainbeat.repositories import membership as membership_repo
from trainbeat.repositories import notification as notification_repo
from trainbeat.repositories import session as session_repo
from trainbeat.repositories import user as user_repo

from ._helpers import init_data_header


async def _seed_trainer_and_athletes(db_session, athlete_count=1):
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    athletes = []
    for i in range(athlete_count):
        a = await user_repo.create(
            db_session, telegram_id=100 + i, name=f"A{i}", role=UserRole.athlete
        )
        await membership_repo.create(
            db_session, group_id=group.id, athlete_id=a.id, status=MembershipStatus.active
        )
        athletes.append(a)
    return coach, group, athletes


@pytest.mark.asyncio
async def test_reminders_created_on_session_creation(http_client, db_session) -> None:
    """Scenario: Reminders scheduled at session creation."""
    _, group, _ = await _seed_trainer_and_athletes(db_session, athlete_count=1)
    when = datetime.now(UTC) + timedelta(hours=48)

    response = await http_client.post(
        "/api/sessions",
        json={"group_id": group.id, "scheduled_at": when.isoformat(), "duration_min": 60},
        headers=init_data_header(1),
    )
    assert response.status_code == 201
    session_id = response.json()[0]["id"]

    rows = await notification_repo.list_for_session(db_session, session_id)
    assert len(rows) == 2
    offsets = sorted([(when - r.scheduled_at).total_seconds() / 3600 for r in rows])
    # Approximately 1h and 24h offsets
    assert 0.9 < offsets[0] < 1.1
    assert 23.9 < offsets[1] < 24.1


@pytest.mark.asyncio
async def test_reminder_delivery_transitions_state(db_session) -> None:
    """Scenario: Reminder delivery transitions state."""
    _, group, _ = await _seed_trainer_and_athletes(db_session, athlete_count=1)
    row = await session_repo.create_one_off(
        db_session,
        group_id=group.id,
        workout_template_id=None,
        scheduled_at=datetime.now(UTC) + timedelta(minutes=30),
        duration_min=60,
    )
    await notification_repo.schedule_session_reminders(
        db_session, session_id=row.id, group_id=group.id, scheduled_at=row.scheduled_at
    )

    sent_count: list[int] = []

    async def fake_sender(user_id: int, payload: str) -> None:
        sent_count.append(user_id)

    delivered = await notification_repo.deliver_due(db_session, sender=fake_sender)
    assert delivered >= 1
    rows = await notification_repo.list_for_session(db_session, row.id)
    sent_rows = [r for r in rows if r.status == NotificationStatus.sent]
    assert len(sent_rows) >= 1


@pytest.mark.asyncio
async def test_reminder_sweep_is_idempotent(db_session) -> None:
    """Scenario: Reminder is idempotent under sweep retries."""
    _, group, _ = await _seed_trainer_and_athletes(db_session, athlete_count=1)
    row = await session_repo.create_one_off(
        db_session,
        group_id=group.id,
        workout_template_id=None,
        scheduled_at=datetime.now(UTC) + timedelta(minutes=30),
        duration_min=60,
    )
    await notification_repo.schedule_session_reminders(
        db_session, session_id=row.id, group_id=group.id, scheduled_at=row.scheduled_at
    )

    calls: list[int] = []

    async def fake_sender(user_id: int, payload: str) -> None:
        calls.append(user_id)

    await notification_repo.deliver_due(db_session, sender=fake_sender)
    first_round = len(calls)
    await notification_repo.deliver_due(db_session, sender=fake_sender)
    assert len(calls) == first_round  # no re-delivery


@pytest.mark.asyncio
async def test_cancel_session_cancels_reminders(http_client, db_session) -> None:
    """Scenario: Cancel before any reminder fires."""
    _, group, _ = await _seed_trainer_and_athletes(db_session, athlete_count=1)
    when = datetime.now(UTC) + timedelta(days=2)

    create_resp = await http_client.post(
        "/api/sessions",
        json={"group_id": group.id, "scheduled_at": when.isoformat(), "duration_min": 60},
        headers=init_data_header(1),
    )
    session_id = create_resp.json()[0]["id"]

    cancel_resp = await http_client.post(
        f"/api/sessions/{session_id}/cancel", headers=init_data_header(1)
    )
    assert cancel_resp.status_code == 200

    rows = await notification_repo.list_for_session(db_session, session_id)
    assert all(r.status == NotificationStatus.cancelled for r in rows)


@pytest.mark.asyncio
async def test_trainer_sends_broadcast(http_client, db_session) -> None:
    """Scenario: Trainer sends a broadcast."""
    _, group, _ = await _seed_trainer_and_athletes(db_session, athlete_count=3)

    response = await http_client.post(
        f"/api/groups/{group.id}/broadcast",
        json={"text": "Bring water"},
        headers=init_data_header(1),
    )
    assert response.status_code == 202
    body = response.json()
    assert body["recipient_count"] == 3


@pytest.mark.asyncio
async def test_broadcast_rate_limit_hit(http_client, db_session) -> None:
    """Scenario: Rate limit hit."""
    _, group, _ = await _seed_trainer_and_athletes(db_session, athlete_count=1)
    for i in range(notification_repo.BROADCAST_RATE_LIMIT):
        resp = await http_client.post(
            f"/api/groups/{group.id}/broadcast",
            json={"text": f"#{i}"},
            headers=init_data_header(1),
        )
        assert resp.status_code == 202, f"send {i} failed: {resp.text}"

    blocked = await http_client.post(
        f"/api/groups/{group.id}/broadcast",
        json={"text": "over"},
        headers=init_data_header(1),
    )
    assert blocked.status_code == 429
