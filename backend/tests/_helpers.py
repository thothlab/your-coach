"""Shared test helpers — fixture factories, header builders."""

import time

from trainbeat.security.init_data import build_init_data

BOT_TOKEN = "test-bot-token-7777777777"


def init_data_header(telegram_id: int, first_name: str = "Test", **extra) -> dict[str, str]:
    user_payload = {"id": telegram_id, "first_name": first_name, **extra}
    raw = build_init_data(
        bot_token=BOT_TOKEN, user=user_payload, auth_date=int(time.time())
    )
    return {"X-Telegram-Init-Data": raw}
