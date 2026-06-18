from datetime import UTC, datetime, timedelta

from dateutil.rrule import rrulestr
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Session, SessionStatus

MAX_MATERIALIZATION_DAYS = 60
MAX_OCCURRENCES_PER_SERIES = 200


def expand_rrule(
    rule: str, *, dtstart: datetime, horizon_days: int = MAX_MATERIALIZATION_DAYS
) -> list[datetime]:
    """Expand an RRULE into concrete datetimes within the horizon window."""
    cutoff = dtstart + timedelta(days=horizon_days)
    rule_obj = rrulestr(rule, dtstart=dtstart)
    out: list[datetime] = []
    for moment in rule_obj:
        if moment > cutoff:
            break
        if len(out) >= MAX_OCCURRENCES_PER_SERIES:
            break
        out.append(moment)
    return out


async def create_one_off(
    session: AsyncSession,
    *,
    group_id: int,
    workout_template_id: int | None,
    scheduled_at: datetime,
    duration_min: int,
) -> Session:
    row = Session(
        group_id=group_id,
        workout_template_id=workout_template_id,
        scheduled_at=scheduled_at,
        duration_min=duration_min,
        status=SessionStatus.scheduled,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def create_recurring(
    session: AsyncSession,
    *,
    group_id: int,
    workout_template_id: int | None,
    scheduled_at: datetime,
    duration_min: int,
    recurrence_rule: str,
) -> list[Session]:
    moments = expand_rrule(recurrence_rule, dtstart=scheduled_at)
    if not moments:
        return []
    rows: list[Session] = []
    for moment in moments:
        row = Session(
            group_id=group_id,
            workout_template_id=workout_template_id,
            scheduled_at=moment,
            duration_min=duration_min,
            recurrence_rule=recurrence_rule,
            status=SessionStatus.scheduled,
        )
        session.add(row)
        rows.append(row)
    await session.commit()
    for row in rows:
        await session.refresh(row)
    return rows


async def get(session: AsyncSession, session_id: int) -> Session | None:
    return await session.get(Session, session_id)


async def cancel(session: AsyncSession, row: Session) -> None:
    row.status = SessionStatus.cancelled
    await session.commit()


async def list_for_groups(
    session: AsyncSession,
    *,
    group_ids: list[int],
    from_: datetime,
    to: datetime,
) -> list[Session]:
    if not group_ids:
        return []
    stmt = (
        select(Session)
        .where(
            and_(
                Session.group_id.in_(group_ids),
                Session.scheduled_at >= from_,
                Session.scheduled_at <= to,
            )
        )
        .order_by(Session.scheduled_at)
    )
    return list(await session.scalars(stmt))


async def auto_complete_expired(session: AsyncSession, *, now: datetime | None = None) -> int:
    """Set status=completed for any scheduled session past its grace window."""
    current = now or datetime.now(UTC)
    stmt = select(Session).where(Session.status == SessionStatus.scheduled)
    rows = list(await session.scalars(stmt))
    flipped = 0
    for row in rows:
        end = row.scheduled_at + timedelta(minutes=row.duration_min + 24 * 60)
        if end < current:
            row.status = SessionStatus.completed
            flipped += 1
    if flipped:
        await session.commit()
    return flipped
