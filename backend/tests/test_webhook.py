import os

import pytest


def _sample_update() -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 0,
            "chat": {"id": 1, "type": "private"},
            "from": {"id": 1, "is_bot": False, "first_name": "T"},
            "text": "hello",
        },
    }


@pytest.mark.asyncio
async def test_webhook_rejects_missing_secret(http_client) -> None:
    response = await http_client.post("/api/telegram/webhook", json=_sample_update())
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_rejects_wrong_secret(http_client) -> None:
    response = await http_client.post(
        "/api/telegram/webhook",
        json=_sample_update(),
        headers={"X-Telegram-Bot-Api-Secret-Token": "not-the-secret"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_accepts_valid_secret(http_client) -> None:
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "dev-only-secret")
    response = await http_client.post(
        "/api/telegram/webhook",
        json=_sample_update(),
        headers={"X-Telegram-Bot-Api-Secret-Token": secret},
    )
    # The update is well-formed; aiogram's dispatcher accepts unknown messages quietly.
    assert response.status_code == 200
