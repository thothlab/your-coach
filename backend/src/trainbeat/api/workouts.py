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


class ExerciseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    unit: ExerciseUnit | None = None


class ExerciseResponse(BaseModel):
    id: int
    name: str
    unit: str
    media_type: str | None = None
    media_url: str | None = None
    media_file_unique_id: str | None = None


def _exercise_response(ex) -> "ExerciseResponse":
    return ExerciseResponse(
        id=ex.id,
        name=ex.name,
        unit=ex.unit.value,
        media_type=ex.media_type,
        media_url=ex.media_url,
        media_file_unique_id=ex.media_file_unique_id,
    )


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
    return _exercise_response(ex)


@exercises_router.get("", response_model=list[ExerciseResponse])
async def list_exercises(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ExerciseResponse]:
    _require_trainer(user)
    rows = await exercise_repo.list_for_trainer(session, user.id)
    return [_exercise_response(ex) for ex in rows]


@exercises_router.patch("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: int,
    body: ExerciseUpdateRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExerciseResponse:
    _require_trainer(user)
    ex = await exercise_repo.get_owned(
        session, exercise_id=exercise_id, trainer_id=user.id
    )
    if ex is None:
        raise HTTPException(status_code=404, detail="exercise not found")
    if body.unit is not None and body.unit != ex.unit:
        # Changing the unit would invalidate the target rules of any template
        # that already references this exercise — forbid it while in use.
        if await exercise_repo.is_used_in_template(session, exercise_id):
            raise HTTPException(
                status_code=409,
                detail="cannot change unit: exercise is used in a workout template",
            )
        ex.unit = body.unit
    if body.name is not None:
        ex.name = body.name
    await session.commit()
    await session.refresh(ex)
    return _exercise_response(ex)


def _resolve_owned_exercises(
    items: list[TemplateItemRequest],
    owned: dict[int, object],
) -> None:
    """Raise if any item references an exercise the trainer doesn't own, then
    validate each item's targets against its exercise unit."""
    exercise_ids = [item.exercise_id for item in items]
    missing = [eid for eid in exercise_ids if eid not in owned]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"exercises not owned by trainer: {missing}",
        )
    for item in items:
        _validate_item_targets(owned[item.exercise_id].unit, item)


def _template_response(template) -> TemplateResponse:
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


@workouts_router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: TemplateCreateRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TemplateResponse:
    _require_trainer(user)
    owned = await exercise_repo.get_owned_many(
        session, ids=list({item.exercise_id for item in body.items}), trainer_id=user.id
    )
    _resolve_owned_exercises(body.items, owned)
    template = await workout_repo.create_template(
        session,
        trainer_id=user.id,
        name=body.name,
        items=[item.model_dump() for item in body.items],
    )
    return _template_response(template)


@workouts_router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    body: TemplateCreateRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TemplateResponse:
    _require_trainer(user)
    template = await workout_repo.get_owned(
        session, template_id=template_id, trainer_id=user.id
    )
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    owned = await exercise_repo.get_owned_many(
        session, ids=list({item.exercise_id for item in body.items}), trainer_id=user.id
    )
    _resolve_owned_exercises(body.items, owned)
    template = await workout_repo.replace_template(
        session,
        template=template,
        name=body.name,
        items=[item.model_dump() for item in body.items],
    )
    return _template_response(template)


@workouts_router.get("", response_model=list[TemplateResponse])
async def list_templates(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TemplateResponse]:
    _require_trainer(user)
    templates = await workout_repo.list_for_trainer(session, user.id)
    return [_template_response(t) for t in templates]
