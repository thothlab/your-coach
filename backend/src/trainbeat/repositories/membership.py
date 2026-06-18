from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Membership, MembershipStatus


async def list_for_group(
    session: AsyncSession, group_id: int
) -> list[Membership]:
    stmt = select(Membership).where(Membership.group_id == group_id).order_by(
        Membership.joined_at
    )
    return list(await session.scalars(stmt))


async def get(
    session: AsyncSession, *, group_id: int, athlete_id: int
) -> Membership | None:
    stmt = select(Membership).where(
        Membership.group_id == group_id, Membership.athlete_id == athlete_id
    )
    return await session.scalar(stmt)


async def active_group_ids_for_athlete(
    session: AsyncSession, athlete_id: int
) -> set[int]:
    stmt = select(Membership.group_id).where(
        Membership.athlete_id == athlete_id,
        Membership.status == MembershipStatus.active,
    )
    return set(await session.scalars(stmt))


async def activate_pending_for_athlete(
    session: AsyncSession, athlete_id: int
) -> int:
    stmt = (
        update(Membership)
        .where(
            Membership.athlete_id == athlete_id,
            Membership.status == MembershipStatus.pending,
        )
        .values(status=MembershipStatus.active)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


async def remove(session: AsyncSession, *, group_id: int, athlete_id: int) -> bool:
    stmt = (
        update(Membership)
        .where(
            Membership.group_id == group_id,
            Membership.athlete_id == athlete_id,
            Membership.status == MembershipStatus.active,
        )
        .values(status=MembershipStatus.removed)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def create(
    session: AsyncSession,
    *,
    group_id: int,
    athlete_id: int,
    status: MembershipStatus = MembershipStatus.pending,
) -> Membership:
    membership = Membership(group_id=group_id, athlete_id=athlete_id, status=status)
    session.add(membership)
    await session.commit()
    return membership
