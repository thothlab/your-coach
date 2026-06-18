import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import SessionLocal
from .models import UserRole
from .repositories import invite as invite_repo
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


def build_invite_url(token: str) -> str:
    return f"https://t.me/{settings.telegram_bot_username}?start={token}"


async def onboard_no_payload(
    session: AsyncSession, *, telegram_id: int, display_name: str
) -> tuple[str, bool]:
    """Decide how to respond to /start without a payload.

    Returns (reply_text, include_open_app_button).
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


async def redeem_invite(
    session: AsyncSession, *, token: str, telegram_id: int, display_name: str
) -> tuple[str, bool]:
    """Decide how to respond to /start <token>.

    Returns (reply_text, include_open_app_button).
    """
    try:
        await invite_repo.redeem(
            session, token=token, telegram_id=telegram_id, telegram_name=display_name
        )
    except invite_repo.InviteNotFound:
        return ("This invite link is not recognized.", False)
    except invite_repo.InviteAlreadyUsed:
        return ("This invite has already been used.", False)
    except invite_repo.InviteExpired:
        return ("This invite has expired.", False)
    except invite_repo.PersonalSlotTaken:
        return ("Personal slot already taken.", False)
    return (
        "You're in. Open the app to see your schedule and confirm sessions.",
        True,
    )


@dp.message(CommandStart(deep_link=True))
async def handle_start_with_token(message: Message, command: CommandObject) -> None:
    if message.from_user is None or command.args is None:
        return
    display_name = (
        message.from_user.full_name or message.from_user.username or "Athlete"
    )
    async with SessionLocal() as session:
        reply_text, with_button = await redeem_invite(
            session,
            token=command.args.strip(),
            telegram_id=message.from_user.id,
            display_name=display_name,
        )
    await message.answer(
        reply_text, reply_markup=_open_app_keyboard() if with_button else None
    )


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
