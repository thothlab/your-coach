from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import WorkoutLog


async def next_set_index(
    session: AsyncSession,
    *,
    session_id: int,
    athlete_id: int,
    exercise_id: int,
) -> int:
    stmt = select(func.max(WorkoutLog.set_index)).where(
        WorkoutLog.session_id == session_id,
        WorkoutLog.athlete_id == athlete_id,
        WorkoutLog.exercise_id == exercise_id,
    )
    current_max = await session.scalar(stmt)
    return 1 if current_max is None else int(current_max) + 1


async def append(
    session: AsyncSession,
    *,
    session_id: int,
    athlete_id: int,
    exercise_id: int,
    set_index: int,
    actual_reps: int | None = None,
    actual_weight: Decimal | None = None,
    actual_seconds: int | None = None,
    note: str | None = None,
) -> WorkoutLog:
    row = WorkoutLog(
        session_id=session_id,
        athlete_id=athlete_id,
        exercise_id=exercise_id,
        set_index=set_index,
        actual_reps=actual_reps,
        actual_weight=actual_weight,
        actual_seconds=actual_seconds,
        note=note,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_for_session(
    session: AsyncSession, session_id: int
) -> list[WorkoutLog]:
    stmt = (
        select(WorkoutLog)
        .where(WorkoutLog.session_id == session_id)
        .order_by(WorkoutLog.athlete_id, WorkoutLog.exercise_id, WorkoutLog.set_index)
    )
    return list(await session.scalars(stmt))


async def list_for_athlete_in_session(
    session: AsyncSession, *, session_id: int, athlete_id: int
) -> list[WorkoutLog]:
    stmt = (
        select(WorkoutLog)
        .where(
            WorkoutLog.session_id == session_id, WorkoutLog.athlete_id == athlete_id
        )
        .order_by(WorkoutLog.exercise_id, WorkoutLog.set_index)
    )
    return list(await session.scalars(stmt))
