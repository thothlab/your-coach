from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_session
from ..repositories import user as user_repo
from ..security.init_data import InitDataError, parse_and_validate

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthResponse(BaseModel):
    user_id: int
    telegram_id: int
    name: str
    role: str


@router.post("/telegram", response_model=AuthResponse)
async def authenticate(
    x_telegram_init_data: Annotated[str, Header(alias="X-Telegram-Init-Data")],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    try:
        init_data = parse_and_validate(
            x_telegram_init_data, bot_token=settings.telegram_bot_token
        )
    except InitDataError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = await user_repo.get_by_telegram_id(session, init_data.user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not registered — start the bot first",
        )

    return AuthResponse(
        user_id=user.id,
        telegram_id=user.telegram_id,
        name=user.name,
        role=user.role.value,
    )
