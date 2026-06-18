from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import AttendanceStatus, SessionStatus, User, UserRole
from ..repositories import attendance as attendance_repo
from ..repositories import group as group_repo
from ..repositories import membership as membership_repo
from ..repositories import notification as notification_repo
from ..repositories import session as session_repo
from ..repositories import workout as workout_repo
from ..repositories import workout_log as workout_log_repo
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
        await attendance_repo.initialize_for_session(
            session, session_id=row.id, group_id=body.group_id
        )
        await notification_repo.schedule_session_reminders(
            session,
            session_id=row.id,
            group_id=body.group_id,
            scheduled_at=row.scheduled_at,
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
    for row in rows:
        await attendance_repo.initialize_for_session(
            session, session_id=row.id, group_id=body.group_id
        )
        await notification_repo.schedule_session_reminders(
            session,
            session_id=row.id,
            group_id=body.group_id,
            scheduled_at=row.scheduled_at,
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
    await notification_repo.cancel_for_session(session, session_id)
    return {"status": "cancelled"}


class AthleteAttendanceRequest(BaseModel):
    status: AttendanceStatus  # confirmed | declined


class TrainerAttendanceRequest(BaseModel):
    status: AttendanceStatus  # present | absent


class WorkoutLogCreateRequest(BaseModel):
    exercise_id: int
    set_index: int = Field(..., ge=1)
    actual_reps: int | None = None
    actual_weight: float | None = None
    actual_seconds: int | None = None
    note: str | None = None


class WorkoutLogResponse(BaseModel):
    id: int
    session_id: int
    athlete_id: int
    exercise_id: int
    set_index: int
    actual_reps: int | None
    actual_weight: float | None
    actual_seconds: int | None
    note: str | None


@router.post("/{session_id}/attendance", status_code=200)
async def set_own_attendance(
    session_id: int,
    body: AthleteAttendanceRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    if body.status not in (AttendanceStatus.confirmed, AttendanceStatus.declined):
        raise HTTPException(status_code=400, detail="status must be confirmed or declined")
    row = await session_repo.get(session, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="session not found")
    end = row.scheduled_at + timedelta(minutes=row.duration_min)
    if datetime.now(UTC) >= end:
        raise HTTPException(status_code=409, detail="session already past")

    att = await attendance_repo.get(session, session_id=session_id, athlete_id=user.id)
    if att is None:
        raise HTTPException(status_code=403, detail="not a member of this session")
    await attendance_repo.set_status(session, att, body.status)
    return {"status": body.status.value}


@router.post("/{session_id}/attendance/{athlete_id}", status_code=200)
async def set_attendee_attendance(
    session_id: int,
    athlete_id: int,
    body: TrainerAttendanceRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    if user.role != UserRole.trainer:
        raise HTTPException(status_code=403, detail="trainer role required")
    if body.status not in (AttendanceStatus.present, AttendanceStatus.absent):
        raise HTTPException(status_code=400, detail="status must be present or absent")

    row = await session_repo.get(session, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="session not found")
    group = await group_repo.get(session, row.group_id)
    if group is None or group.trainer_id != user.id:
        raise HTTPException(status_code=404, detail="session not found")
    if datetime.now(UTC) < row.scheduled_at:
        raise HTTPException(status_code=409, detail="session has not started yet")

    att = await attendance_repo.get(
        session, session_id=session_id, athlete_id=athlete_id
    )
    if att is None:
        raise HTTPException(status_code=404, detail="attendance row not found")
    await attendance_repo.set_status(session, att, body.status)

    # Auto-complete when every active member is present/absent
    if await attendance_repo.all_finalized(session, session_id):
        row.status = SessionStatus.completed
        await session.commit()

    return {"status": body.status.value}


@router.post("/{session_id}/log", response_model=WorkoutLogResponse, status_code=201)
async def append_log(
    session_id: int,
    body: WorkoutLogCreateRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkoutLogResponse:
    row = await session_repo.get(session, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="session not found")

    # Athletes log own; trainer can log anyone (used in trainer-led classes)
    if user.role == UserRole.athlete:
        att = await attendance_repo.get(
            session, session_id=session_id, athlete_id=user.id
        )
        if att is None or att.status not in (
            AttendanceStatus.confirmed,
            AttendanceStatus.present,
        ):
            raise HTTPException(
                status_code=403, detail="must be confirmed or present to log"
            )
        target_athlete_id = user.id
    else:
        group = await group_repo.get(session, row.group_id)
        if group is None or group.trainer_id != user.id:
            raise HTTPException(status_code=404, detail="session not found")
        # Trainer log defaults to themselves? No — require explicit athlete via separate endpoint.
        # For MVP we keep the simple case: trainer can log own
        target_athlete_id = user.id

    expected = await workout_log_repo.next_set_index(
        session,
        session_id=session_id,
        athlete_id=target_athlete_id,
        exercise_id=body.exercise_id,
    )
    if body.set_index != expected:
        raise HTTPException(
            status_code=400,
            detail=f"out of order; next expected set_index is {expected}",
        )

    from decimal import Decimal as _D

    log = await workout_log_repo.append(
        session,
        session_id=session_id,
        athlete_id=target_athlete_id,
        exercise_id=body.exercise_id,
        set_index=body.set_index,
        actual_reps=body.actual_reps,
        actual_weight=_D(str(body.actual_weight)) if body.actual_weight is not None else None,
        actual_seconds=body.actual_seconds,
        note=body.note,
    )
    return WorkoutLogResponse(
        id=log.id,
        session_id=log.session_id,
        athlete_id=log.athlete_id,
        exercise_id=log.exercise_id,
        set_index=log.set_index,
        actual_reps=log.actual_reps,
        actual_weight=float(log.actual_weight) if log.actual_weight is not None else None,
        actual_seconds=log.actual_seconds,
        note=log.note,
    )


@router.get("/{session_id}/log", response_model=list[WorkoutLogResponse])
async def get_log(
    session_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[WorkoutLogResponse]:
    row = await session_repo.get(session, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="session not found")
    if user.role == UserRole.trainer:
        group = await group_repo.get(session, row.group_id)
        if group is None or group.trainer_id != user.id:
            raise HTTPException(status_code=404, detail="session not found")
        logs = await workout_log_repo.list_for_session(session, session_id)
    else:
        logs = await workout_log_repo.list_for_athlete_in_session(
            session, session_id=session_id, athlete_id=user.id
        )
    return [
        WorkoutLogResponse(
            id=log.id,
            session_id=log.session_id,
            athlete_id=log.athlete_id,
            exercise_id=log.exercise_id,
            set_index=log.set_index,
            actual_reps=log.actual_reps,
            actual_weight=float(log.actual_weight) if log.actual_weight is not None else None,
            actual_seconds=log.actual_seconds,
            note=log.note,
        )
        for log in logs
    ]


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
