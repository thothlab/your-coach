from fastapi import HTTPException, Request

from ..config import settings
from ..db import SessionLocal
from ..models import User, UserRole
from ..repositories import user as user_repo
from ..security.init_data import InitDataError, parse_and_validate


def current_user(request: Request) -> User:
    user: User | None = getattr(request.state, "current_user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user


async def trainer_from_init_data(request: Request) -> User:
    """Authenticate a trainer from the X-Telegram-Init-Data header.

    Used by routes that live outside the /api prefix (e.g. multipart upload),
    which the global TelegramAuthMiddleware does not cover.
    """
    raw = request.headers.get("X-Telegram-Init-Data")
    if not raw:
        raise HTTPException(status_code=401, detail="missing init data")
    try:
        init_data = parse_and_validate(raw, bot_token=settings.telegram_bot_token)
    except InitDataError as exc:
        raise HTTPException(status_code=401, detail=f"init data invalid: {exc}") from exc
    async with SessionLocal() as session:
        user = await user_repo.get_by_telegram_id(session, init_data.user.id)
    if user is None:
        raise HTTPException(status_code=401, detail="user not registered")
    if user.role != UserRole.trainer:
        raise HTTPException(status_code=403, detail="trainer role required")
    return user
