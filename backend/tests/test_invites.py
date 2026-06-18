import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from trainbeat.bot import redeem_invite
from trainbeat.db import SessionLocal
from trainbeat.models import GroupType, Invite, MembershipStatus, UserRole
from trainbeat.repositories import group as group_repo
from trainbeat.repositories import invite as invite_repo
from trainbeat.repositories import membership as membership_repo
from trainbeat.repositories import user as user_repo

from ._helpers import init_data_header


@pytest.mark.asyncio
async def test_trainer_creates_invite_via_api(http_client, db_session) -> None:
    """Scenario: Trainer generates invite from bot (via API)."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="Coach", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )

    response = await http_client.post(
        f"/api/groups/{group.id}/invites", headers=init_data_header(1)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["url"].startswith("https://t.me/trainbeat_bot?start=")
    assert len(body["token"]) >= 32
    assert "expires_at" in body


@pytest.mark.asyncio
async def test_create_invite_rejects_foreign_group(http_client, db_session) -> None:
    me = await user_repo.create(
        db_session, telegram_id=1, name="Me", role=UserRole.trainer
    )
    other = await user_repo.create(
        db_session, telegram_id=2, name="Other", role=UserRole.trainer
    )
    foreign = await group_repo.create(
        db_session, trainer_id=other.id, name="Theirs", type=GroupType.group
    )

    response = await http_client.post(
        f"/api/groups/{foreign.id}/invites", headers=init_data_header(1)
    )
    assert response.status_code == 404
    assert me.id != other.id


@pytest.mark.asyncio
async def test_athlete_cannot_create_invite(http_client, db_session) -> None:
    athlete = await user_repo.create(
        db_session, telegram_id=1, name="A", role=UserRole.athlete
    )
    response = await http_client.post(
        f"/api/groups/{athlete.id}/invites", headers=init_data_header(1)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_fresh_redemption_creates_athlete_and_pending_membership(db_session) -> None:
    """Scenario: Fresh athlete redeems valid invite."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    invite = await invite_repo.create(
        db_session, trainer_id=coach.id, group_id=group.id
    )

    reply, with_button = await redeem_invite(
        db_session, token=invite.token, telegram_id=42, display_name="Anna"
    )

    assert with_button is True
    assert "You're in" in reply
    athlete = await user_repo.get_by_telegram_id(db_session, 42)
    assert athlete is not None
    assert athlete.role == UserRole.athlete
    membership = await membership_repo.get(
        db_session, group_id=group.id, athlete_id=athlete.id
    )
    assert membership is not None
    assert membership.status == MembershipStatus.pending
    # invite consumed
    fresh_invite = await db_session.scalar(
        select(Invite).where(Invite.id == invite.id)
    )
    await db_session.refresh(fresh_invite)
    assert fresh_invite.used_at is not None
    assert fresh_invite.used_by_user_id == athlete.id


@pytest.mark.asyncio
async def test_reused_token_rejected(db_session) -> None:
    """Scenario: Reused token is rejected."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    invite = await invite_repo.create(
        db_session, trainer_id=coach.id, group_id=group.id
    )
    await redeem_invite(db_session, token=invite.token, telegram_id=42, display_name="A")

    reply, with_button = await redeem_invite(
        db_session, token=invite.token, telegram_id=43, display_name="B"
    )

    assert with_button is False
    assert "already been used" in reply
    assert await user_repo.get_by_telegram_id(db_session, 43) is None


@pytest.mark.asyncio
async def test_expired_token_rejected(db_session) -> None:
    """Scenario: Expired token is rejected."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    invite = await invite_repo.create(
        db_session, trainer_id=coach.id, group_id=group.id
    )
    invite.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()

    reply, with_button = await redeem_invite(
        db_session, token=invite.token, telegram_id=44, display_name="X"
    )

    assert with_button is False
    assert "expired" in reply
    assert await user_repo.get_by_telegram_id(db_session, 44) is None


@pytest.mark.asyncio
async def test_unknown_token_rejected(db_session) -> None:
    reply, with_button = await redeem_invite(
        db_session, token="not-a-real-token", telegram_id=1, display_name="Y"
    )
    assert with_button is False
    assert "not recognized" in reply


@pytest.mark.asyncio
async def test_concurrent_personal_redemption_only_one_wins(db_session) -> None:
    """Scenario: Two athletes redeem invites to the same personal group."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    personal = await group_repo.create(
        db_session, trainer_id=coach.id, name="P", type=GroupType.personal
    )
    inv1 = await invite_repo.create(
        db_session, trainer_id=coach.id, group_id=personal.id
    )
    inv2 = await invite_repo.create(
        db_session, trainer_id=coach.id, group_id=personal.id
    )

    async def redeem_with_own_session(token: str, tg_id: int) -> tuple[str, bool]:
        async with SessionLocal() as s:
            return await redeem_invite(
                s, token=token, telegram_id=tg_id, display_name=f"A{tg_id}"
            )

    results = await asyncio.gather(
        redeem_with_own_session(inv1.token, 100),
        redeem_with_own_session(inv2.token, 101),
        return_exceptions=True,
    )

    successes = [r for r in results if isinstance(r, tuple) and r[1] is True]
    rejections = [r for r in results if isinstance(r, tuple) and r[1] is False]

    assert len(successes) == 1
    assert len(rejections) == 1
    assert "Personal slot already taken" in rejections[0][0]
