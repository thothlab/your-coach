from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Attendance, AttendanceStatus, Membership, MembershipStatus


async def initialize_for_session(
    session: AsyncSession, *, session_id: int, group_id: int
) -> int:
    stmt = select(Membership.athlete_id).where(
        Membership.group_id == group_id,
        Membership.status == MembershipStatus.active,
    )
    athlete_ids = list(await session.scalars(stmt))
    for athlete_id in athlete_ids:
        session.add(
            Attendance(
                session_id=session_id,
                athlete_id=athlete_id,
                status=AttendanceStatus.pending,
            )
        )
    if athlete_ids:
        await session.commit()
    return len(athlete_ids)


async def get(
    session: AsyncSession, *, session_id: int, athlete_id: int
) -> Attendance | None:
    stmt = select(Attendance).where(
        Attendance.session_id == session_id, Attendance.athlete_id == athlete_id
    )
    return await session.scalar(stmt)


async def list_for_session(session: AsyncSession, session_id: int) -> list[Attendance]:
    stmt = select(Attendance).where(Attendance.session_id == session_id)
    return list(await session.scalars(stmt))


async def set_status(
    session: AsyncSession, row: Attendance, status: AttendanceStatus
) -> None:
    row.status = status
    row.updated_at = datetime.now(UTC)
    await session.commit()


async def all_finalized(session: AsyncSession, session_id: int) -> bool:
    """True iff every attendance row is present or absent."""
    rows = await list_for_session(session, session_id)
    if not rows:
        return False
    return all(r.status in (AttendanceStatus.present, AttendanceStatus.absent) for r in rows)
