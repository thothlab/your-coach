from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_session
from ..models import GroupType, User, UserRole
from ..repositories import group as group_repo
from ..repositories import invite as invite_repo
from ..repositories import membership as membership_repo
from ..repositories import notification as notification_repo
from .deps import current_user

router = APIRouter(prefix="/api/groups", tags=["groups"])


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: GroupType


class GroupResponse(BaseModel):
    id: int
    name: str
    type: str
    active_member_count: int


class MemberResponse(BaseModel):
    athlete_id: int
    name: str
    status: str


class InviteResponse(BaseModel):
    token: str
    url: str
    expires_at: str


class BroadcastRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class BroadcastResponse(BaseModel):
    recipient_count: int


def _require_trainer(user: User) -> None:
    if user.role != UserRole.trainer:
        raise HTTPException(status_code=403, detail="trainer role required")


@router.post("", response_model=GroupResponse, status_code=201)
async def create_group(
    body: GroupCreateRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GroupResponse:
    _require_trainer(user)
    group = await group_repo.create(
        session, trainer_id=user.id, name=body.name, type=body.type
    )
    return GroupResponse(
        id=group.id, name=group.name, type=group.type.value, active_member_count=0
    )


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[GroupResponse]:
    _require_trainer(user)
    groups = await group_repo.list_for_trainer(session, user.id)
    out: list[GroupResponse] = []
    for group in groups:
        count = await group_repo.count_active_members(session, group.id)
        out.append(
            GroupResponse(
                id=group.id,
                name=group.name,
                type=group.type.value,
                active_member_count=count,
            )
        )
    return out


@router.get("/{group_id}/members", response_model=list[MemberResponse])
async def list_members(
    group_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MemberResponse]:
    _require_trainer(user)
    group = await group_repo.get(session, group_id)
    if group is None or group.trainer_id != user.id:
        raise HTTPException(status_code=404, detail="group not found")
    memberships = await membership_repo.list_for_group(session, group_id)
    if not memberships:
        return []
    ids = {m.athlete_id for m in memberships}
    rows = await session.scalars(select(User).where(User.id.in_(ids)))
    names = {u.id: u.name for u in rows}
    return [
        MemberResponse(
            athlete_id=m.athlete_id,
            name=names.get(m.athlete_id, ""),
            status=m.status.value,
        )
        for m in memberships
    ]


@router.post("/{group_id}/invites", response_model=InviteResponse, status_code=201)
async def create_invite(
    group_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InviteResponse:
    _require_trainer(user)
    group = await group_repo.get(session, group_id)
    if group is None or group.trainer_id != user.id:
        raise HTTPException(status_code=404, detail="group not found")
    invite = await invite_repo.create(
        session, trainer_id=user.id, group_id=group_id
    )
    url = f"https://t.me/{settings.telegram_bot_username}?start={invite.token}"
    return InviteResponse(
        token=invite.token,
        url=url,
        expires_at=invite.expires_at.isoformat(),
    )


@router.post(
    "/{group_id}/broadcast", response_model=BroadcastResponse, status_code=202
)
async def broadcast(
    group_id: int,
    body: BroadcastRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BroadcastResponse:
    _require_trainer(user)
    group = await group_repo.get(session, group_id)
    if group is None or group.trainer_id != user.id:
        raise HTTPException(status_code=404, detail="group not found")

    memberships = await membership_repo.list_for_group(session, group_id)
    active_ids = [
        m.athlete_id for m in memberships if m.status.value == "active"
    ]

    sent_in_window = await notification_repo.broadcast_count_in_window(
        session,
        group_member_ids=active_ids,
        window_seconds=int(notification_repo.BROADCAST_WINDOW.total_seconds()),
    )
    # Rate limit: each broadcast creates len(active_ids) rows. So divide.
    member_count = max(1, len(active_ids))
    broadcasts_so_far = sent_in_window // member_count
    if broadcasts_so_far >= notification_repo.BROADCAST_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="broadcast rate limit exceeded")

    await notification_repo.schedule_broadcast(
        session, group_member_ids=active_ids, text=body.text
    )
    return BroadcastResponse(recipient_count=len(active_ids))


@router.delete("/{group_id}/members/{athlete_id}", status_code=204)
async def remove_member(
    group_id: int,
    athlete_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    _require_trainer(user)
    group = await group_repo.get(session, group_id)
    if group is None or group.trainer_id != user.id:
        raise HTTPException(status_code=404, detail="group not found")
    removed = await membership_repo.remove(
        session, group_id=group_id, athlete_id=athlete_id
    )
    if not removed:
        raise HTTPException(status_code=404, detail="active membership not found")
