import time

import pytest
from sqlalchemy import select

from trainbeat.bot import (
    INVITE_CALLBACK_PREFIX,
    INVITE_PICKER_TTL_SECONDS,
    InviteCreated,
    InviteCreateGroupFirst,
    InvitePickerNeeded,
    InvitePickExpired,
    InvitePickForbidden,
    InvitePickResolved,
    apply_invite_pick,
    decode_invite_callback,
    encode_invite_callback,
    prepare_invite_response,
)
from trainbeat.models import GroupType, Invite, UserRole
from trainbeat.repositories import group as group_repo
from trainbeat.repositories import user as user_repo


@pytest.mark.asyncio
async def test_single_group_auto_creates(db_session) -> None:
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    await group_repo.create(
        db_session, trainer_id=coach.id, name="Solo", type=GroupType.group
    )

    result = await prepare_invite_response(db_session, telegram_id=1)

    assert isinstance(result, InviteCreated)
    assert "https://t.me/" in result.url


@pytest.mark.asyncio
async def test_zero_groups_redirects(db_session) -> None:
    await user_repo.create(db_session, telegram_id=1, name="C", role=UserRole.trainer)

    result = await prepare_invite_response(db_session, telegram_id=1)

    assert isinstance(result, InviteCreateGroupFirst)


@pytest.mark.asyncio
async def test_multiple_groups_show_picker(db_session) -> None:
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    g1 = await group_repo.create(
        db_session, trainer_id=coach.id, name="G1", type=GroupType.group
    )
    g2 = await group_repo.create(
        db_session, trainer_id=coach.id, name="G2", type=GroupType.group
    )
    g3 = await group_repo.create(
        db_session, trainer_id=coach.id, name="G3", type=GroupType.group
    )

    result = await prepare_invite_response(db_session, telegram_id=1, now=1_000_000)

    assert isinstance(result, InvitePickerNeeded)
    ids = {g.id for g in result.groups}
    assert ids == {g1.id, g2.id, g3.id}
    assert result.timestamp == 1_000_000


@pytest.mark.asyncio
async def test_picker_tap_creates_invite(db_session) -> None:
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    now = int(time.time())

    result = await apply_invite_pick(
        db_session,
        telegram_id=1,
        group_id=group.id,
        picker_timestamp=now - 60,
        now=now,
    )

    assert isinstance(result, InvitePickResolved)
    invite = await db_session.scalar(select(Invite).where(Invite.group_id == group.id))
    assert invite is not None
    assert invite.used_at is None


@pytest.mark.asyncio
async def test_picker_tap_after_expiry(db_session) -> None:
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    now = int(time.time())

    result = await apply_invite_pick(
        db_session,
        telegram_id=1,
        group_id=group.id,
        picker_timestamp=now - (INVITE_PICKER_TTL_SECONDS + 60),
        now=now,
    )

    assert isinstance(result, InvitePickExpired)
    invite = await db_session.scalar(select(Invite).where(Invite.group_id == group.id))
    assert invite is None


@pytest.mark.asyncio
async def test_picker_tap_forbidden_for_other_trainer(db_session) -> None:
    me = await user_repo.create(
        db_session, telegram_id=1, name="Me", role=UserRole.trainer
    )
    other = await user_repo.create(
        db_session, telegram_id=2, name="Other", role=UserRole.trainer
    )
    foreign = await group_repo.create(
        db_session, trainer_id=other.id, name="Theirs", type=GroupType.group
    )
    now = int(time.time())

    result = await apply_invite_pick(
        db_session,
        telegram_id=1,
        group_id=foreign.id,
        picker_timestamp=now,
        now=now,
    )

    assert isinstance(result, InvitePickForbidden)
    assert me.id != other.id


def test_callback_round_trip() -> None:
    data = encode_invite_callback(42, 1_700_000_000)
    assert data.startswith(f"{INVITE_CALLBACK_PREFIX}:")
    parsed = decode_invite_callback(data)
    assert parsed == (42, 1_700_000_000)


def test_decode_rejects_bad_payload() -> None:
    assert decode_invite_callback("xxx:1:2") is None
    assert decode_invite_callback(f"{INVITE_CALLBACK_PREFIX}:bad:1") is None
    assert decode_invite_callback(f"{INVITE_CALLBACK_PREFIX}:1") is None
