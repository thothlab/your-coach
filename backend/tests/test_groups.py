import pytest

from trainbeat.models import GroupType, MembershipStatus, UserRole
from trainbeat.repositories import group as group_repo
from trainbeat.repositories import membership as membership_repo
from trainbeat.repositories import user as user_repo

from ._helpers import init_data_header


@pytest.mark.asyncio
async def test_trainer_creates_group(http_client, db_session) -> None:
    """Scenario: Trainer creates a group."""
    await user_repo.create(db_session, telegram_id=1, name="Coach", role=UserRole.trainer)

    response = await http_client.post(
        "/api/groups",
        json={"name": "Monday strength", "type": "group"},
        headers=init_data_header(1),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Monday strength"
    assert body["type"] == "group"
    assert body["active_member_count"] == 0


@pytest.mark.asyncio
async def test_trainer_creates_personal_slot(http_client, db_session) -> None:
    """Scenario: Trainer creates a personal slot."""
    await user_repo.create(db_session, telegram_id=1, name="Coach", role=UserRole.trainer)

    response = await http_client.post(
        "/api/groups",
        json={"name": "Anna — personal", "type": "personal"},
        headers=init_data_header(1),
    )

    assert response.status_code == 201
    assert response.json()["type"] == "personal"


@pytest.mark.asyncio
async def test_athlete_cannot_create_group(http_client, db_session) -> None:
    await user_repo.create(db_session, telegram_id=2, name="Athlete", role=UserRole.athlete)

    response = await http_client.post(
        "/api/groups",
        json={"name": "X", "type": "group"},
        headers=init_data_header(2),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_groups_returns_trainer_own(http_client, db_session) -> None:
    coach = await user_repo.create(
        db_session, telegram_id=1, name="Coach", role=UserRole.trainer
    )
    other = await user_repo.create(
        db_session, telegram_id=99, name="OtherCoach", role=UserRole.trainer
    )
    await group_repo.create(db_session, trainer_id=coach.id, name="Mine", type=GroupType.group)
    await group_repo.create(db_session, trainer_id=other.id, name="Theirs", type=GroupType.group)

    response = await http_client.get("/api/groups", headers=init_data_header(1))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Mine"


@pytest.mark.asyncio
async def test_first_authed_call_activates_pending_membership(
    http_client, db_session
) -> None:
    """Scenario: Athlete first opens the Mini-App."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="Coach", role=UserRole.trainer
    )
    athlete = await user_repo.create(
        db_session, telegram_id=2, name="Anna", role=UserRole.athlete
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    await membership_repo.create(
        db_session, group_id=group.id, athlete_id=athlete.id, status=MembershipStatus.pending
    )

    # First authed call by athlete
    response = await http_client.get("/api/me", headers=init_data_header(2))
    assert response.status_code == 200

    await db_session.commit()  # flush any prior tx
    fresh = await membership_repo.get(db_session, group_id=group.id, athlete_id=athlete.id)
    await db_session.refresh(fresh)
    assert fresh.status == MembershipStatus.active


@pytest.mark.asyncio
async def test_trainer_removes_athlete(http_client, db_session) -> None:
    """Scenario: Trainer removes an athlete."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="Coach", role=UserRole.trainer
    )
    athlete = await user_repo.create(
        db_session, telegram_id=2, name="Anna", role=UserRole.athlete
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    await membership_repo.create(
        db_session, group_id=group.id, athlete_id=athlete.id, status=MembershipStatus.active
    )

    response = await http_client.delete(
        f"/api/groups/{group.id}/members/{athlete.id}",
        headers=init_data_header(1),
    )
    assert response.status_code == 204

    fresh = await membership_repo.get(db_session, group_id=group.id, athlete_id=athlete.id)
    await db_session.refresh(fresh)
    assert fresh.status == MembershipStatus.removed


@pytest.mark.asyncio
async def test_trainer_cannot_touch_other_trainer_group(http_client, db_session) -> None:
    me = await user_repo.create(
        db_session, telegram_id=1, name="Me", role=UserRole.trainer
    )
    other = await user_repo.create(
        db_session, telegram_id=2, name="Other", role=UserRole.trainer
    )
    foreign_group = await group_repo.create(
        db_session, trainer_id=other.id, name="Theirs", type=GroupType.group
    )

    response = await http_client.get(
        f"/api/groups/{foreign_group.id}/members",
        headers=init_data_header(1),
    )
    assert response.status_code == 404
    assert me.id != other.id  # silences ruff


@pytest.mark.asyncio
async def test_list_members_returns_full_membership_list(http_client, db_session) -> None:
    coach = await user_repo.create(
        db_session, telegram_id=1, name="Coach", role=UserRole.trainer
    )
    athlete = await user_repo.create(
        db_session, telegram_id=2, name="Anna", role=UserRole.athlete
    )
    group = await group_repo.create(
        db_session, trainer_id=coach.id, name="G", type=GroupType.group
    )
    await membership_repo.create(
        db_session, group_id=group.id, athlete_id=athlete.id, status=MembershipStatus.active
    )

    response = await http_client.get(
        f"/api/groups/{group.id}/members",
        headers=init_data_header(1),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["athlete_id"] == athlete.id
    assert body[0]["name"] == "Anna"
    assert body[0]["status"] == "active"
