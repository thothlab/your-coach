from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import WorkoutTemplate, WorkoutTemplateItem


async def create_template(
    session: AsyncSession,
    *,
    trainer_id: int,
    name: str,
    items: list[dict],
) -> WorkoutTemplate:
    template = WorkoutTemplate(trainer_id=trainer_id, name=name)
    for index, item in enumerate(items, start=1):
        template.items.append(
            WorkoutTemplateItem(
                position=index,
                exercise_id=item["exercise_id"],
                sets=item["sets"],
                target_reps=item.get("target_reps"),
                target_weight=(
                    Decimal(str(item["target_weight"]))
                    if item.get("target_weight") is not None
                    else None
                ),
                target_seconds=item.get("target_seconds"),
            )
        )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def replace_template(
    session: AsyncSession,
    *,
    template: WorkoutTemplate,
    name: str,
    items: list[dict],
) -> WorkoutTemplate:
    """Rename a template and replace all its items.

    Safe to delete+recreate items: nothing references workout_template_items by
    id (sessions point at the template as a whole; logs reference exercises).
    """
    template.name = name
    template.items.clear()  # delete-orphan cascade removes the old rows
    # Flush the DELETEs before the INSERTs: positions are reused (1..n) and the
    # unique constraint (template_id, position) would otherwise collide because
    # SQLAlchemy's unit of work orders INSERTs ahead of DELETEs within a flush.
    await session.flush()
    for index, item in enumerate(items, start=1):
        template.items.append(
            WorkoutTemplateItem(
                position=index,
                exercise_id=item["exercise_id"],
                sets=item["sets"],
                target_reps=item.get("target_reps"),
                target_weight=(
                    Decimal(str(item["target_weight"]))
                    if item.get("target_weight") is not None
                    else None
                ),
                target_seconds=item.get("target_seconds"),
            )
        )
    await session.commit()
    await session.refresh(template)
    return template


async def list_for_trainer(
    session: AsyncSession, trainer_id: int
) -> list[WorkoutTemplate]:
    stmt = (
        select(WorkoutTemplate)
        .where(WorkoutTemplate.trainer_id == trainer_id)
        .order_by(WorkoutTemplate.created_at.desc())
    )
    return list(await session.scalars(stmt))


async def get_owned(
    session: AsyncSession, *, template_id: int, trainer_id: int
) -> WorkoutTemplate | None:
    stmt = select(WorkoutTemplate).where(
        WorkoutTemplate.id == template_id, WorkoutTemplate.trainer_id == trainer_id
    )
    return await session.scalar(stmt)
