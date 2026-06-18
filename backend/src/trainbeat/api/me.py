from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..models import User
from .deps import current_user

router = APIRouter(prefix="/api", tags=["me"])


class MeResponse(BaseModel):
    id: int
    telegram_id: int
    name: str
    role: str


@router.get("/me", response_model=MeResponse)
async def get_me(user: Annotated[User, Depends(current_user)]) -> MeResponse:
    return MeResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        name=user.name,
        role=user.role.value,
    )
