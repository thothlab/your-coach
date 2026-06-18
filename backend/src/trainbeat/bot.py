import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from .config import settings

logger = logging.getLogger(__name__)
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    # Real onboarding lands in Task 02 (identity-and-auth).
    await message.answer("TrainBeat is awake. Onboarding wires up in Task 02.")


async def start_bot() -> None:
    bot = Bot(settings.telegram_bot_token)
    logger.info("bot polling started")
    await dp.start_polling(bot)
