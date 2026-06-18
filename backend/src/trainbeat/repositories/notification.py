import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Membership,
    MembershipStatus,
    Notification,
    NotificationKind,
    NotificationStatus,
)

REMINDER_OFFSETS = [timedelta(hours=24), timedelta(hours=1)]
BROADCAST_RATE_LIMIT = 5
BROADCAST_WINDOW = timedelta(hours=24)


async def schedule_session_reminders(
    db: AsyncSession, *, session_id: int, group_id: int, scheduled_at: datetime
) -> int:
    """Insert reminder rows for every active member of the group.

    Uses ON CONFLICT DO NOTHING to make the call idempotent against the
    (user_id, session_id, kind, scheduled_at) UNIQUE constraint.
    """
    stmt = select(Membership.athlete_id).where(
        Membership.group_id == group_id,
        Membership.status == MembershipStatus.active,
    )
    athlete_ids = list(await db.scalars(stmt))
    if not athlete_ids:
        return 0
    rows: list[dict] = []
    for athlete_id in athlete_ids:
        for offset in REMINDER_OFFSETS:
            rows.append(
                {
                    "user_id": athlete_id,
                    "session_id": session_id,
                    "kind": NotificationKind.reminder.value,
                    "scheduled_at": scheduled_at - offset,
                    "status": NotificationStatus.scheduled.value,
                    "payload": json.dumps({"session_id": session_id}),
                }
            )
    if not rows:
        return 0
    stmt = pg_insert(Notification).values(rows).on_conflict_do_nothing()
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0


async def cancel_for_session(db: AsyncSession, session_id: int) -> int:
    stmt = select(Notification).where(
        Notification.session_id == session_id,
        Notification.status == NotificationStatus.scheduled,
    )
    rows = list(await db.scalars(stmt))
    for row in rows:
        row.status = NotificationStatus.cancelled
    if rows:
        await db.commit()
    return len(rows)


async def deliver_due(
    db: AsyncSession,
    *,
    sender: Callable[[int, str], Awaitable[None]],
    now: datetime | None = None,
    limit: int = 500,
) -> int:
    current = now or datetime.now(UTC)
    stmt = (
        select(Notification)
        .where(
            and_(
                Notification.scheduled_at <= current,
                Notification.status == NotificationStatus.scheduled,
            )
        )
        .order_by(Notification.scheduled_at)
        .limit(limit)
    )
    rows = list(await db.scalars(stmt))
    sent = 0
    for row in rows:
        try:
            await sender(row.user_id, row.payload)
        except Exception:  # noqa: BLE001 — caller decides retry policy
            continue
        row.status = NotificationStatus.sent
        row.sent_at = datetime.now(UTC)
        sent += 1
    if sent:
        await db.commit()
    return sent


async def list_for_session(db: AsyncSession, session_id: int) -> list[Notification]:
    stmt = select(Notification).where(Notification.session_id == session_id)
    return list(await db.scalars(stmt))


async def broadcast_count_in_window(
    db: AsyncSession, *, group_member_ids: list[int], window_seconds: int
) -> int:
    if not group_member_ids:
        return 0
    cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
    stmt = (
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id.in_(group_member_ids),
            Notification.kind == NotificationKind.broadcast,
            Notification.scheduled_at >= cutoff,
        )
    )
    return await db.scalar(stmt) or 0


async def schedule_broadcast(
    db: AsyncSession, *, group_member_ids: list[int], text: str
) -> int:
    if not group_member_ids:
        return 0
    now = datetime.now(UTC)
    rows: list[dict] = []
    for index, user_id in enumerate(group_member_ids):
        rows.append(
            {
                "user_id": user_id,
                "session_id": None,
                "kind": NotificationKind.broadcast.value,
                # Distinct scheduled_at per row to avoid clashing on UNIQUE.
                "scheduled_at": now + timedelta(microseconds=index),
                "status": NotificationStatus.scheduled.value,
                "payload": json.dumps({"text": text}),
            }
        )
    stmt = pg_insert(Notification).values(rows).on_conflict_do_nothing()
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or len(rows)
