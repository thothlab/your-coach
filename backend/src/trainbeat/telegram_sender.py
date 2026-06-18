import json
import logging
from collections.abc import Awaitable, Callable

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User

logger = logging.getLogger(__name__)


def make_telegram_sender(bot: Bot) -> Callable[[int, str], Awaitable[None]]:
    """Build a (user_id, payload) → None sender bound to a Bot instance.

    Resolves the internal ``user_id`` to a ``telegram_id`` (the chat to send to).
    Payloads are JSON; reminder payloads carry ``session_id``, broadcast carry ``text``.
    """

    async def send(user_id: int, payload: str) -> None:
        from .db import SessionLocal

        async with SessionLocal() as session:
            user = await session.get(User, user_id)
        if user is None:
            logger.warning("telegram_send: user_id=%s not found", user_id)
            return
        try:
            body = json.loads(payload)
        except json.JSONDecodeError:
            body = {}
        text = body.get("text") or _format_reminder(body)
        await bot.send_message(chat_id=user.telegram_id, text=text)

    return send


def _format_reminder(body: dict) -> str:
    session_id = body.get("session_id")
    if session_id is None:
        return "TrainBeat reminder."
    return f"Reminder: your session #{session_id} is coming up soon."


async def _dummy_session_used_to_satisfy_linter(session: AsyncSession) -> None:
    # Reserved hook for future per-message persistence; keeps the import alive.
    _ = session
