import time

import pytest

from trainbeat.bot import onboard_no_payload
from trainbeat.models import UserRole
from trainbeat.repositories import user as user_repo
from trainbeat.security.init_data import build_init_data

BOT_TOKEN = "test-bot-token-7777777777"


@pytest.mark.asyncio
async def test_first_start_creates_trainer(db_session) -> None:
    """Scenario: First message creates a trainer."""
    reply, with_button = await onboard_no_payload(
        db_session, telegram_id=111, display_name="Anna"
    )

    user = await user_repo.get_by_telegram_id(db_session, 111)
    assert user is not None
    assert user.role == UserRole.trainer
    assert user.name == "Anna"
    assert "Welcome to TrainBeat" in reply
    assert with_button is True


@pytest.mark.asyncio
async def test_returning_trainer_gets_welcome_back(db_session) -> None:
    await user_repo.create(db_session, telegram_id=222, name="Bob", role=UserRole.trainer)

    reply, with_button = await onboard_no_payload(
        db_session, telegram_id=222, display_name="Bob (renamed)"
    )

    assert "Welcome back, Bob" in reply
    assert with_button is True
    user = await user_repo.get_by_telegram_id(db_session, 222)
    assert user.name == "Bob"  # immutable on /start, only updated by explicit flow


@pytest.mark.asyncio
async def test_second_user_without_invite_is_not_created(db_session) -> None:
    """Scenario: Second user without invite is treated as athlete-pending."""
    await user_repo.create(db_session, telegram_id=222, name="Bob", role=UserRole.trainer)

    reply, with_button = await onboard_no_payload(
        db_session, telegram_id=333, display_name="Carol"
    )

    assert "Ask your trainer for an invite link" in reply
    assert with_button is False
    assert await user_repo.get_by_telegram_id(db_session, 333) is None


@pytest.mark.asyncio
async def test_tampered_init_data_rejected_by_api(http_client) -> None:
    """Scenario: Tampered initData is rejected."""
    raw = build_init_data(
        bot_token=BOT_TOKEN,
        user={"id": 555, "first_name": "X"},
        auth_date=int(time.time()),
    )
    tampered = raw[:-4] + "abcd"

    response = await http_client.get("/api/me", headers={"X-Telegram-Init-Data": tampered})

    assert response.status_code == 401
    assert "init data invalid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_stale_init_data_rejected_by_api(http_client) -> None:
    """Scenario: Stale initData is rejected."""
    raw = build_init_data(
        bot_token=BOT_TOKEN,
        user={"id": 555, "first_name": "X"},
        auth_date=int(time.time()) - 86400 - 1,
    )

    response = await http_client.get("/api/me", headers={"X-Telegram-Init-Data": raw})

    assert response.status_code == 401
    assert "stale" in response.json()["detail"]


@pytest.mark.asyncio
async def test_missing_init_data_rejected_by_api(http_client) -> None:
    response = await http_client.get("/api/me")
    assert response.status_code == 401
    assert "missing init data" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unregistered_user_rejected_by_api(http_client) -> None:
    raw = build_init_data(
        bot_token=BOT_TOKEN,
        user={"id": 999, "first_name": "Unknown"},
        auth_date=int(time.time()),
    )
    response = await http_client.get("/api/me", headers={"X-Telegram-Init-Data": raw})
    assert response.status_code == 401
    assert response.json()["detail"] == "user not registered"


@pytest.mark.asyncio
async def test_post_auth_telegram_returns_user(http_client, db_session) -> None:
    await user_repo.create(db_session, telegram_id=42, name="Anna", role=UserRole.trainer)
    raw = build_init_data(
        bot_token=BOT_TOKEN,
        user={"id": 42, "first_name": "Anna"},
        auth_date=int(time.time()),
    )

    response = await http_client.post(
        "/api/auth/telegram", headers={"X-Telegram-Init-Data": raw}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["telegram_id"] == 42
    assert body["name"] == "Anna"
    assert body["role"] == "trainer"


@pytest.mark.asyncio
async def test_post_auth_telegram_rejects_unknown_user(http_client) -> None:
    raw = build_init_data(
        bot_token=BOT_TOKEN,
        user={"id": 7, "first_name": "Ghost"},
        auth_date=int(time.time()),
    )
    response = await http_client.post(
        "/api/auth/telegram", headers={"X-Telegram-Init-Data": raw}
    )
    assert response.status_code == 401
    assert "not registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_returns_authenticated_user(http_client, db_session) -> None:
    await user_repo.create(db_session, telegram_id=42, name="Anna", role=UserRole.trainer)
    raw = build_init_data(
        bot_token=BOT_TOKEN,
        user={"id": 42, "first_name": "Anna"},
        auth_date=int(time.time()),
    )

    response = await http_client.get("/api/me", headers={"X-Telegram-Init-Data": raw})

    assert response.status_code == 200
    body = response.json()
    assert body["telegram_id"] == 42
    assert body["role"] == "trainer"
