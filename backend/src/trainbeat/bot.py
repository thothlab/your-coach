import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import SessionLocal
from .models import UserRole
from .repositories import user as user_repo

logger = logging.getLogger(__name__)
dp = Dispatcher()


def _open_app_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Open app",
                    web_app=WebAppInfo(url=settings.telegram_webapp_url),
                )
            ]
        ]
    )


async def onboard_no_payload(
    session: AsyncSession, *, telegram_id: int, display_name: str
) -> tuple[str, bool]:
    """Decide how to respond to /start without a payload.

    Returns (reply_text, include_open_app_button).
    Pure-ish: only depends on the supplied session; trivially testable.
    """
    existing = await user_repo.get_by_telegram_id(session, telegram_id)
    if existing is not None:
        return (
            f"Welcome back, {existing.name}. Open the app to continue ({existing.role.value}).",
            True,
        )

    total = await user_repo.count_users(session)
    if total == 0:
        user = await user_repo.create(
            session, telegram_id=telegram_id, name=display_name, role=UserRole.trainer
        )
        return (
            f"Welcome to TrainBeat, {user.name}. "
            "You're set up as a trainer — open the app to create groups and invite athletes.",
            True,
        )

    return ("Ask your trainer for an invite link, then tap it to join.", False)


@dp.message(CommandStart(deep_link=False))
async def handle_start_no_payload(message: Message) -> None:
    if message.from_user is None:
        return
    display_name = (
        message.from_user.full_name or message.from_user.username or "Trainer"
    )
    async with SessionLocal() as session:
        reply_text, with_button = await onboard_no_payload(
            session, telegram_id=message.from_user.id, display_name=display_name
        )
    await message.answer(
        reply_text, reply_markup=_open_app_keyboard() if with_button else None
    )


async def start_bot() -> None:
    bot = Bot(settings.telegram_bot_token)
    logger.info("bot polling started")
    await dp.start_polling(bot)
