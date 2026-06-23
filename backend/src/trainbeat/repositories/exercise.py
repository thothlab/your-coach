from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Exercise, ExerciseUnit, WorkoutTemplateItem


async def create(
    session: AsyncSession, *, trainer_id: int, name: str, unit: ExerciseUnit
) -> Exercise:
    exercise = Exercise(trainer_id=trainer_id, name=name, unit=unit)
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise


async def is_used_in_template(session: AsyncSession, exercise_id: int) -> bool:
    """True if any workout template references this exercise (blocks unit change)."""
    stmt = select(WorkoutTemplateItem.id).where(
        WorkoutTemplateItem.exercise_id == exercise_id
    ).limit(1)
    return await session.scalar(stmt) is not None


async def list_for_trainer(session: AsyncSession, trainer_id: int) -> list[Exercise]:
    stmt = (
        select(Exercise).where(Exercise.trainer_id == trainer_id).order_by(Exercise.name)
    )
    return list(await session.scalars(stmt))


async def get_owned(
    session: AsyncSession, *, exercise_id: int, trainer_id: int
) -> Exercise | None:
    stmt = select(Exercise).where(
        Exercise.id == exercise_id, Exercise.trainer_id == trainer_id
    )
    return await session.scalar(stmt)


async def get_by_media_unique_id(
    session: AsyncSession, file_unique_id: str
) -> Exercise | None:
    stmt = select(Exercise).where(Exercise.media_file_unique_id == file_unique_id)
    return await session.scalar(stmt)


async def get_owned_many(
    session: AsyncSession, *, ids: list[int], trainer_id: int
) -> dict[int, Exercise]:
    if not ids:
        return {}
    stmt = select(Exercise).where(
        Exercise.id.in_(ids), Exercise.trainer_id == trainer_id
    )
    rows = await session.scalars(stmt)
    return {ex.id: ex for ex in rows}
