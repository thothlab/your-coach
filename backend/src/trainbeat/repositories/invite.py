import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Group,
    GroupType,
    Invite,
    Membership,
    MembershipStatus,
    User,
    UserRole,
)


class InviteError(Exception):
    """Base class for redemption failures."""


class InviteNotFound(InviteError):
    pass


class InviteAlreadyUsed(InviteError):
    pass


class InviteExpired(InviteError):
    pass


class PersonalSlotTaken(InviteError):
    pass


async def create(
    session: AsyncSession,
    *,
    trainer_id: int,
    group_id: int,
    ttl_days: int = 7,
) -> Invite:
    invite = Invite(
        token=secrets.token_urlsafe(32),
        trainer_id=trainer_id,
        group_id=group_id,
        expires_at=datetime.now(UTC) + timedelta(days=ttl_days),
    )
    session.add(invite)
    await session.commit()
    await session.refresh(invite)
    return invite


async def redeem(
    session: AsyncSession,
    *,
    token: str,
    telegram_id: int,
    telegram_name: str,
) -> tuple[Invite, User, Membership]:
    """Atomically redeem an invite.

    Locks the invite and group rows to serialize concurrent redemptions on the
    same personal group (PRD invariant: max 1 non-removed membership for a
    personal group).
    """
    invite = await session.scalar(
        select(Invite).where(Invite.token == token).with_for_update()
    )
    if invite is None:
        raise InviteNotFound()
    if invite.used_at is not None:
        raise InviteAlreadyUsed()
    if invite.expires_at < datetime.now(UTC):
        raise InviteExpired()

    group = await session.scalar(
        select(Group).where(Group.id == invite.group_id).with_for_update()
    )
    if group is None:
        raise InviteError("group not found")

    if group.type == GroupType.personal:
        existing = await session.scalar(
            select(func.count())
            .select_from(Membership)
            .where(
                Membership.group_id == group.id,
                Membership.status != MembershipStatus.removed,
            )
        )
        if existing and existing > 0:
            raise PersonalSlotTaken()

    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, name=telegram_name, role=UserRole.athlete)
        session.add(user)
        await session.flush()

    membership = Membership(
        group_id=group.id, athlete_id=user.id, status=MembershipStatus.pending
    )
    session.add(membership)

    invite.used_at = datetime.now(UTC)
    invite.used_by_user_id = user.id

    await session.commit()
    await session.refresh(invite)
    await session.refresh(user)
    return invite, user, membership
