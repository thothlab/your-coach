import time

import pytest

from trainbeat.security.init_data import (
    InitDataError,
    build_init_data,
    parse_and_validate,
)

BOT_TOKEN = "test-bot-token-7777777777"


def _sample_user() -> dict:
    return {"id": 12345, "first_name": "Anna", "last_name": "K", "username": "anna"}


def test_valid_init_data_round_trip() -> None:
    now = int(time.time())
    raw = build_init_data(bot_token=BOT_TOKEN, user=_sample_user(), auth_date=now)
    parsed = parse_and_validate(raw, bot_token=BOT_TOKEN)
    assert parsed.user.id == 12345
    assert parsed.user.first_name == "Anna"
    assert parsed.auth_date == now


def test_tampered_hash_rejected() -> None:
    raw = build_init_data(bot_token=BOT_TOKEN, user=_sample_user(), auth_date=int(time.time()))
    tampered = raw[:-4] + "abcd"
    with pytest.raises(InitDataError, match="hash mismatch"):
        parse_and_validate(tampered, bot_token=BOT_TOKEN)


def test_wrong_bot_token_rejected() -> None:
    raw = build_init_data(bot_token=BOT_TOKEN, user=_sample_user(), auth_date=int(time.time()))
    with pytest.raises(InitDataError, match="hash mismatch"):
        parse_and_validate(raw, bot_token="different-token-1111111111")


def test_stale_init_data_rejected() -> None:
    old = int(time.time()) - 86400 - 1
    raw = build_init_data(bot_token=BOT_TOKEN, user=_sample_user(), auth_date=old)
    with pytest.raises(InitDataError, match="stale"):
        parse_and_validate(raw, bot_token=BOT_TOKEN)


def test_future_auth_date_rejected() -> None:
    future = int(time.time()) + 600
    raw = build_init_data(bot_token=BOT_TOKEN, user=_sample_user(), auth_date=future)
    with pytest.raises(InitDataError, match="future"):
        parse_and_validate(raw, bot_token=BOT_TOKEN)


def test_missing_hash_rejected() -> None:
    with pytest.raises(InitDataError, match="missing hash"):
        parse_and_validate("user=%7B%22id%22%3A1%7D&auth_date=1", bot_token=BOT_TOKEN)


def test_empty_raw_rejected() -> None:
    with pytest.raises(InitDataError, match="empty"):
        parse_and_validate("", bot_token=BOT_TOKEN)


def test_start_param_preserved() -> None:
    now = int(time.time())
    raw = build_init_data(
        bot_token=BOT_TOKEN, user=_sample_user(), auth_date=now, start_param="invite_xyz"
    )
    parsed = parse_and_validate(raw, bot_token=BOT_TOKEN)
    assert parsed.start_param == "invite_xyz"
