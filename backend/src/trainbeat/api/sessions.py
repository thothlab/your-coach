from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import SessionStatus, User, UserRole
from ..repositories import group as group_repo
from ..repositories import membership as membership_repo
from ..repositories import session as session_repo
from ..repositories import workout as workout_repo
from .deps import current_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionCreateRequest(BaseModel):
    group_id: int
    workout_template_id: int | None = None
    scheduled_at: datetime
    duration_min: int = Field(..., ge=5, le=600)
    recurrence_rule: str | None = None


class SessionResponse(BaseModel):
    id: int
    group_id: int
    workout_template_id: int | None
    scheduled_at: datetime
    duration_min: int
    status: str
    recurrence_rule: str | None


def _to_response(row) -> SessionResponse:
    return SessionResponse(
        id=row.id,
        group_id=row.group_id,
        workout_template_id=row.workout_template_id,
        scheduled_at=row.scheduled_at,
        duration_min=row.duration_min,
        status=row.status.value,
        recurrence_rule=row.recurrence_rule,
    )


@router.post("", response_model=list[SessionResponse], status_code=201)
async def create_session(
    body: SessionCreateRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SessionResponse]:
    if user.role != UserRole.trainer:
        raise HTTPException(status_code=403, detail="trainer role required")

    group = await group_repo.get(session, body.group_id)
    if group is None or group.trainer_id != user.id:
        raise HTTPException(status_code=404, detail="group not found")

    if body.workout_template_id is not None:
        template = await workout_repo.get_owned(
            session, template_id=body.workout_template_id, trainer_id=user.id
        )
        if template is None:
            raise HTTPException(
                status_code=404, detail="workout template not found"
            )

    now = datetime.now(UTC)
    scheduled = (
        body.scheduled_at
        if body.scheduled_at.tzinfo
        else body.scheduled_at.replace(tzinfo=UTC)
    )
    if scheduled < now:
        raise HTTPException(status_code=400, detail="scheduled_at is in the past")

    if body.recurrence_rule is None:
        row = await session_repo.create_one_off(
            session,
            group_id=body.group_id,
            workout_template_id=body.workout_template_id,
            scheduled_at=scheduled,
            duration_min=body.duration_min,
        )
        return [_to_response(row)]

    rows = await session_repo.create_recurring(
        session,
        group_id=body.group_id,
        workout_template_id=body.workout_template_id,
        scheduled_at=scheduled,
        duration_min=body.duration_min,
        recurrence_rule=body.recurrence_rule,
    )
    return [_to_response(row) for row in rows]


@router.post("/{session_id}/cancel", status_code=200)
async def cancel_session(
    session_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    if user.role != UserRole.trainer:
        raise HTTPException(status_code=403, detail="trainer role required")

    row = await session_repo.get(session, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="session not found")
    group = await group_repo.get(session, row.group_id)
    if group is None or group.trainer_id != user.id:
        raise HTTPException(status_code=404, detail="session not found")
    if row.status != SessionStatus.scheduled:
        raise HTTPException(
            status_code=409, detail=f"cannot cancel session with status {row.status.value}"
        )
    await session_repo.cancel(session, row)
    return {"status": "cancelled"}


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    from_: Annotated[datetime, Query(alias="from")],
    to: Annotated[datetime, Query()],
) -> list[SessionResponse]:
    from_ = from_ if from_.tzinfo else from_.replace(tzinfo=UTC)
    to = to if to.tzinfo else to.replace(tzinfo=UTC)

    if user.role == UserRole.trainer:
        groups = await group_repo.list_for_trainer(session, user.id)
        group_ids = [g.id for g in groups]
    else:
        group_ids = list(
            await membership_repo.active_group_ids_for_athlete(session, user.id)
        )

    rows = await session_repo.list_for_groups(
        session, group_ids=group_ids, from_=from_, to=to
    )
    return [_to_response(row) for row in rows]
