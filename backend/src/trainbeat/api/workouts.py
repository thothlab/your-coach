from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import ExerciseUnit, User, UserRole
from ..repositories import exercise as exercise_repo
from ..repositories import workout as workout_repo
from .deps import current_user

exercises_router = APIRouter(prefix="/api/exercises", tags=["exercises"])
workouts_router = APIRouter(prefix="/api/workouts", tags=["workouts"])


class ExerciseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    unit: ExerciseUnit


class ExerciseResponse(BaseModel):
    id: int
    name: str
    unit: str


class TemplateItemRequest(BaseModel):
    exercise_id: int
    sets: int = Field(..., ge=1, le=99)
    target_reps: int | None = Field(default=None, ge=1)
    target_weight: Decimal | None = Field(default=None, ge=0)
    target_seconds: int | None = Field(default=None, ge=1)


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    items: list[TemplateItemRequest] = Field(..., min_length=1)


class TemplateItemResponse(BaseModel):
    exercise_id: int
    position: int
    sets: int
    target_reps: int | None
    target_weight: Decimal | None
    target_seconds: int | None


class TemplateResponse(BaseModel):
    id: int
    name: str
    items: list[TemplateItemResponse]


def _require_trainer(user: User) -> None:
    if user.role != UserRole.trainer:
        raise HTTPException(status_code=403, detail="trainer role required")


def _validate_item_targets(unit: ExerciseUnit, item: TemplateItemRequest) -> None:
    if unit == ExerciseUnit.reps:
        if item.target_reps is None:
            raise HTTPException(
                status_code=400,
                detail=f"unit=reps requires target_reps (exercise {item.exercise_id})",
            )
        if item.target_seconds is not None:
            raise HTTPException(
                status_code=400,
                detail=f"unit=reps forbids target_seconds (exercise {item.exercise_id})",
            )
    elif unit == ExerciseUnit.kg:
        eid = item.exercise_id
        if item.target_reps is None or item.target_weight is None:
            raise HTTPException(
                status_code=400,
                detail=f"unit=kg requires target_reps + target_weight (exercise {eid})",
            )
        if item.target_seconds is not None:
            raise HTTPException(
                status_code=400,
                detail=f"unit=kg forbids target_seconds (exercise {eid})",
            )
    elif unit == ExerciseUnit.seconds:
        eid = item.exercise_id
        if item.target_seconds is None:
            raise HTTPException(
                status_code=400,
                detail=f"unit=seconds requires target_seconds (exercise {eid})",
            )
        if item.target_reps is not None or item.target_weight is not None:
            raise HTTPException(
                status_code=400,
                detail=f"unit=seconds forbids reps/weight (exercise {eid})",
            )
    elif unit == ExerciseUnit.meters:
        eid = item.exercise_id
        if item.target_reps is None and item.target_seconds is None:
            raise HTTPException(
                status_code=400,
                detail=f"unit=meters requires target_reps or target_seconds (exercise {eid})",
            )


@exercises_router.post("", response_model=ExerciseResponse, status_code=201)
async def create_exercise(
    body: ExerciseCreateRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExerciseResponse:
    _require_trainer(user)
    ex = await exercise_repo.create(session, trainer_id=user.id, name=body.name, unit=body.unit)
    return ExerciseResponse(id=ex.id, name=ex.name, unit=ex.unit.value)


@exercises_router.get("", response_model=list[ExerciseResponse])
async def list_exercises(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ExerciseResponse]:
    _require_trainer(user)
    rows = await exercise_repo.list_for_trainer(session, user.id)
    return [ExerciseResponse(id=ex.id, name=ex.name, unit=ex.unit.value) for ex in rows]


@workouts_router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: TemplateCreateRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TemplateResponse:
    _require_trainer(user)
    exercise_ids = [item.exercise_id for item in body.items]
    owned = await exercise_repo.get_owned_many(
        session, ids=list(set(exercise_ids)), trainer_id=user.id
    )
    missing = [eid for eid in exercise_ids if eid not in owned]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"exercises not owned by trainer: {missing}",
        )

    for item in body.items:
        _validate_item_targets(owned[item.exercise_id].unit, item)

    template = await workout_repo.create_template(
        session,
        trainer_id=user.id,
        name=body.name,
        items=[item.model_dump() for item in body.items],
    )
    return TemplateResponse(
        id=template.id,
        name=template.name,
        items=[
            TemplateItemResponse(
                exercise_id=i.exercise_id,
                position=i.position,
                sets=i.sets,
                target_reps=i.target_reps,
                target_weight=i.target_weight,
                target_seconds=i.target_seconds,
            )
            for i in template.items
        ],
    )


@workouts_router.get("", response_model=list[TemplateResponse])
async def list_templates(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TemplateResponse]:
    _require_trainer(user)
    templates = await workout_repo.list_for_trainer(session, user.id)
    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            items=[
                TemplateItemResponse(
                    exercise_id=i.exercise_id,
                    position=i.position,
                    sets=i.sets,
                    target_reps=i.target_reps,
                    target_weight=i.target_weight,
                    target_seconds=i.target_seconds,
                )
                for i in t.items
            ],
        )
        for t in templates
    ]
