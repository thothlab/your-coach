import logging
import time
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import SessionLocal
from .models import Group, UserRole
from .repositories import group as group_repo
from .repositories import invite as invite_repo
from .repositories import user as user_repo

INVITE_PICKER_TTL_SECONDS = 5 * 60
INVITE_CALLBACK_PREFIX = "inv"

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


@dataclass(frozen=True)
class InviteCreated:
    url: str


@dataclass(frozen=True)
class InvitePickerNeeded:
    groups: list[Group]
    timestamp: int


@dataclass(frozen=True)
class InviteCreateGroupFirst:
    pass


@dataclass(frozen=True)
class InviteForbidden:
    reason: str


InviteResponse = (
    InviteCreated | InvitePickerNeeded | InviteCreateGroupFirst | InviteForbidden
)


async def prepare_invite_response(
    session: AsyncSession, *, telegram_id: int, now: int | None = None
) -> InviteResponse:
    user = await user_repo.get_by_telegram_id(session, telegram_id)
    if user is None or user.role != UserRole.trainer:
        return InviteForbidden("only trainers can issue invites")
    groups = await group_repo.list_for_trainer(session, user.id)
    if not groups:
        return InviteCreateGroupFirst()
    if len(groups) == 1:
        invite = await invite_repo.create(
            session, trainer_id=user.id, group_id=groups[0].id
        )
        return InviteCreated(url=build_invite_url(invite.token))
    return InvitePickerNeeded(groups=groups, timestamp=now or int(time.time()))


def encode_invite_callback(group_id: int, timestamp: int) -> str:
    return f"{INVITE_CALLBACK_PREFIX}:{group_id}:{timestamp}"


def decode_invite_callback(data: str) -> tuple[int, int] | None:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != INVITE_CALLBACK_PREFIX:
        return None
    try:
        return int(parts[1]), int(parts[2])
    except ValueError:
        return None


@dataclass(frozen=True)
class InvitePickResolved:
    url: str


@dataclass(frozen=True)
class InvitePickExpired:
    pass


@dataclass(frozen=True)
class InvitePickForbidden:
    pass


InvitePickResult = InvitePickResolved | InvitePickExpired | InvitePickForbidden


async def apply_invite_pick(
    session: AsyncSession,
    *,
    telegram_id: int,
    group_id: int,
    picker_timestamp: int,
    now: int | None = None,
) -> InvitePickResult:
    current = now or int(time.time())
    if current - picker_timestamp > INVITE_PICKER_TTL_SECONDS:
        return InvitePickExpired()
    user = await user_repo.get_by_telegram_id(session, telegram_id)
    if user is None or user.role != UserRole.trainer:
        return InvitePickForbidden()
    group = await group_repo.get(session, group_id)
    if group is None or group.trainer_id != user.id:
        return InvitePickForbidden()
    invite = await invite_repo.create(
        session, trainer_id=user.id, group_id=group_id
    )
    return InvitePickResolved(url=build_invite_url(invite.token))


def build_invite_picker_keyboard(
    groups: list[Group], timestamp: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=group.name,
                    callback_data=encode_invite_callback(group.id, timestamp),
                )
            ]
            for group in groups
        ]
    )


@dp.message(Command("invite"))
async def handle_invite(message: Message) -> None:
    if message.from_user is None:
        return
    async with SessionLocal() as session:
        result = await prepare_invite_response(
            session, telegram_id=message.from_user.id
        )
    match result:
        case InviteCreated(url=url):
            await message.answer(f"Invite link:\n{url}")
        case InvitePickerNeeded(groups=groups, timestamp=timestamp):
            await message.answer(
                "Pick a group for the invite:",
                reply_markup=build_invite_picker_keyboard(groups, timestamp),
            )
        case InviteCreateGroupFirst():
            await message.answer(
                "Create a group first — open the app and tap 'Create group'.",
                reply_markup=_open_app_keyboard(),
            )
        case InviteForbidden(reason=reason):
            await message.answer(reason)


@dp.callback_query(F.data.startswith(f"{INVITE_CALLBACK_PREFIX}:"))
async def handle_invite_pick(query: CallbackQuery) -> None:
    if query.from_user is None or query.data is None or query.message is None:
        await query.answer()
        return
    decoded = decode_invite_callback(query.data)
    if decoded is None:
        await query.answer("bad callback", show_alert=False)
        return
    group_id, timestamp = decoded
    async with SessionLocal() as session:
        result = await apply_invite_pick(
            session,
            telegram_id=query.from_user.id,
            group_id=group_id,
            picker_timestamp=timestamp,
        )
    match result:
        case InvitePickResolved(url=url):
            await query.message.edit_text(f"Invite link:\n{url}")
            await query.answer()
        case InvitePickExpired():
            await query.message.edit_text(
                "Selection expired — send /invite again."
            )
            await query.answer()
        case InvitePickForbidden():
            await query.answer("Forbidden", show_alert=False)


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
