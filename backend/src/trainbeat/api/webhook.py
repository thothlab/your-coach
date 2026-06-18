import logging
from typing import Annotated

from aiogram import Bot
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

from ..bot import dp
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[
        str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")
    ] = None,
) -> dict[str, str]:
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="invalid webhook secret")
    payload = await request.json()
    update = Update.model_validate(payload)
    bot = request.app.state.bot if hasattr(request.app.state, "bot") else None
    if bot is None:
        bot = Bot(settings.telegram_bot_token)
        request.app.state.bot = bot
    await dp.feed_update(bot, update)
    return {"status": "ok"}
