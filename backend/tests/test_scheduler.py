from datetime import UTC, datetime, timedelta

import pytest

from trainbeat.models import GroupType, MembershipStatus, UserRole
from trainbeat.repositories import group as group_repo
from trainbeat.repositories import membership as membership_repo
from trainbeat.repositories import notification as notification_repo
from trainbeat.repositories import session as session_repo
from trainbeat.repositories import user as user_repo
from trainbeat.scheduler import build_scheduler


@pytest.mark.asyncio
async def test_scheduler_has_a_notification_sweep_job() -> None:
    async def noop(_user_id: int, _payload: str) -> None:
        return None

    scheduler = build_scheduler(noop)
    job = scheduler.get_job("notification_sweep")
    assert job is not None
    assert job.trigger.interval.total_seconds() >= 60


@pytest.mark.asyncio
async def test_scheduler_tick_delivers_reminders(db_session) -> None:
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
        db_session, group_id=group.id, athlete_id=athlete.id, status=MembershipStatus.active
    )
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

    sent: list[int] = []

    async def sender(user_id: int, _payload: str) -> None:
        sent.append(user_id)

    # Skip apscheduler timing — invoke the sweep directly the same way the job does.
    delivered = await notification_repo.deliver_due(db_session, sender=sender)
    assert delivered >= 1
    assert athlete.id in sent
