from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import settings
from .db import SessionLocal
from .models import UserRole
from .repositories import membership as membership_repo
from .repositories import user as user_repo
from .security.init_data import InitDataError, parse_and_validate

PROTECTED_PREFIX = "/api"
UNPROTECTED_API_PATHS = frozenset({"/api/auth/telegram"})


class TelegramAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith(PROTECTED_PREFIX) or path in UNPROTECTED_API_PATHS:
            return await call_next(request)

        raw = request.headers.get("X-Telegram-Init-Data")
        if not raw:
            return JSONResponse({"detail": "missing init data"}, status_code=401)

        try:
            init_data = parse_and_validate(raw, bot_token=settings.telegram_bot_token)
        except InitDataError as exc:
            return JSONResponse({"detail": f"init data invalid: {exc}"}, status_code=401)

        async with SessionLocal() as session:
            user = await user_repo.get_by_telegram_id(session, init_data.user.id)
            if user is None:
                return JSONResponse({"detail": "user not registered"}, status_code=401)
            if user.role == UserRole.athlete:
                # Auto-activate pending memberships on first authenticated call.
                await membership_repo.activate_pending_for_athlete(session, user.id)

        request.state.current_user = user
        return await call_next(request)
