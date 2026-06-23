"""Lazily-instantiated Bot singleton for use inside API request handlers.

aiogram's Bot creates its aiohttp session on first API call, binding to the
running event loop — so it must be instantiated lazily from within the async
request context, not at import time. A second Bot alongside the polling one
(same token) is fine.
"""

from aiogram import Bot

from .config import settings

_bot: Bot | None = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(settings.telegram_bot_token)
    return _bot
