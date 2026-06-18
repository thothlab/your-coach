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
