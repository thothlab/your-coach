from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Group, GroupType, Membership, MembershipStatus


async def create(
    session: AsyncSession, *, trainer_id: int, name: str, type: GroupType
) -> Group:
    group = Group(trainer_id=trainer_id, name=name, type=type)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


async def get(session: AsyncSession, group_id: int) -> Group | None:
    return await session.get(Group, group_id)


async def list_for_trainer(session: AsyncSession, trainer_id: int) -> list[Group]:
    stmt = select(Group).where(Group.trainer_id == trainer_id).order_by(Group.created_at)
    return list(await session.scalars(stmt))


async def count_active_members(session: AsyncSession, group_id: int) -> int:
    stmt = select(func.count()).select_from(Membership).where(
        Membership.group_id == group_id,
        Membership.status == MembershipStatus.active,
    )
    return await session.scalar(stmt) or 0
