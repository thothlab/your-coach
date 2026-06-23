import pytest

from trainbeat.models import ExerciseUnit, UserRole
from trainbeat.repositories import exercise as exercise_repo
from trainbeat.repositories import user as user_repo

from ._helpers import init_data_header


@pytest.mark.asyncio
async def test_trainer_creates_exercise(http_client, db_session) -> None:
    """Scenario: Trainer creates an exercise."""
    await user_repo.create(db_session, telegram_id=1, name="C", role=UserRole.trainer)

    response = await http_client.post(
        "/api/exercises",
        json={"name": "Back squat", "unit": "kg"},
        headers=init_data_header(1),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Back squat"
    assert body["unit"] == "kg"


@pytest.mark.asyncio
async def test_athlete_forbidden_from_exercises(http_client, db_session) -> None:
    """Scenario: Athlete cannot create or read trainer-scoped exercises."""
    await user_repo.create(db_session, telegram_id=2, name="A", role=UserRole.athlete)

    get_resp = await http_client.get("/api/exercises", headers=init_data_header(2))
    post_resp = await http_client.post(
        "/api/exercises",
        json={"name": "X", "unit": "reps"},
        headers=init_data_header(2),
    )

    assert get_resp.status_code == 403
    assert post_resp.status_code == 403


@pytest.mark.asyncio
async def test_trainer_creates_template(http_client, db_session) -> None:
    """Scenario: Trainer creates a template."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    e1 = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Squat", unit=ExerciseUnit.kg
    )
    e2 = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Pullup", unit=ExerciseUnit.reps
    )

    response = await http_client.post(
        "/api/workouts",
        json={
            "name": "Leg day",
            "items": [
                {"exercise_id": e1.id, "sets": 4, "target_reps": 8, "target_weight": "80"},
                {"exercise_id": e2.id, "sets": 3, "target_reps": 15},
            ],
        },
        headers=init_data_header(1),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Leg day"
    assert len(body["items"]) == 2
    assert body["items"][0]["exercise_id"] == e1.id
    assert body["items"][0]["position"] == 1
    assert body["items"][1]["exercise_id"] == e2.id
    assert body["items"][1]["position"] == 2


@pytest.mark.asyncio
async def test_template_with_foreign_exercise_rejected(http_client, db_session) -> None:
    """Scenario: Template referencing another trainer's exercise is rejected."""
    me = await user_repo.create(
        db_session, telegram_id=1, name="Me", role=UserRole.trainer
    )
    other = await user_repo.create(
        db_session, telegram_id=2, name="Other", role=UserRole.trainer
    )
    foreign = await exercise_repo.create(
        db_session, trainer_id=other.id, name="X", unit=ExerciseUnit.reps
    )

    response = await http_client.post(
        "/api/workouts",
        json={
            "name": "T",
            "items": [{"exercise_id": foreign.id, "sets": 1, "target_reps": 5}],
        },
        headers=init_data_header(1),
    )

    assert response.status_code == 400
    assert me.id != other.id
    assert "not owned" in response.json()["detail"]


@pytest.mark.asyncio
async def test_template_wrong_target_for_unit_rejected(http_client, db_session) -> None:
    """Scenario: Wrong target for unit."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    plank = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Plank", unit=ExerciseUnit.seconds
    )

    response = await http_client.post(
        "/api/workouts",
        json={
            "name": "Bad",
            "items": [
                {
                    "exercise_id": plank.id,
                    "sets": 3,
                    "target_weight": "40",
                }
            ],
        },
        headers=init_data_header(1),
    )

    assert response.status_code == 400
    assert "seconds" in response.json()["detail"]


@pytest.mark.asyncio
async def test_template_kg_requires_reps_and_weight(http_client, db_session) -> None:
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    bench = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Bench", unit=ExerciseUnit.kg
    )

    # missing target_weight
    response = await http_client.post(
        "/api/workouts",
        json={
            "name": "Bad",
            "items": [{"exercise_id": bench.id, "sets": 3, "target_reps": 5}],
        },
        headers=init_data_header(1),
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_trainer_updates_exercise_name_and_unit(http_client, db_session) -> None:
    """Scenario: Trainer renames an exercise and changes its unit (not yet in use)."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    ex = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Squat", unit=ExerciseUnit.kg
    )

    response = await http_client.patch(
        f"/api/exercises/{ex.id}",
        json={"name": "Front squat", "unit": "reps"},
        headers=init_data_header(1),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Front squat"
    assert body["unit"] == "reps"


@pytest.mark.asyncio
async def test_unit_change_blocked_when_used_in_template(http_client, db_session) -> None:
    """Scenario: Changing unit is forbidden once an exercise is in a template."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    ex = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Squat", unit=ExerciseUnit.kg
    )
    await http_client.post(
        "/api/workouts",
        json={
            "name": "T",
            "items": [{"exercise_id": ex.id, "sets": 3, "target_reps": 5, "target_weight": "60"}],
        },
        headers=init_data_header(1),
    )

    response = await http_client.patch(
        f"/api/exercises/{ex.id}",
        json={"unit": "reps"},
        headers=init_data_header(1),
    )
    assert response.status_code == 409, response.text

    # Renaming is still allowed while in use.
    rename = await http_client.patch(
        f"/api/exercises/{ex.id}",
        json={"name": "Box squat"},
        headers=init_data_header(1),
    )
    assert rename.status_code == 200
    assert rename.json()["name"] == "Box squat"


@pytest.mark.asyncio
async def test_trainer_updates_template_items(http_client, db_session) -> None:
    """Scenario: Trainer edits a template — name and items are fully replaced."""
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    e1 = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Squat", unit=ExerciseUnit.kg
    )
    e2 = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="Pullup", unit=ExerciseUnit.reps
    )
    created = await http_client.post(
        "/api/workouts",
        json={
            "name": "Leg day",
            "items": [{"exercise_id": e1.id, "sets": 4, "target_reps": 8, "target_weight": "80"}],
        },
        headers=init_data_header(1),
    )
    template_id = created.json()["id"]

    response = await http_client.put(
        f"/api/workouts/{template_id}",
        json={
            "name": "Upper day",
            "items": [{"exercise_id": e2.id, "sets": 3, "target_reps": 12}],
        },
        headers=init_data_header(1),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Upper day"
    assert len(body["items"]) == 1
    assert body["items"][0]["exercise_id"] == e2.id
    assert body["items"][0]["position"] == 1

    # The change persisted.
    listing = await http_client.get("/api/workouts", headers=init_data_header(1))
    assert listing.json()[0]["name"] == "Upper day"


@pytest.mark.asyncio
async def test_update_foreign_template_rejected(http_client, db_session) -> None:
    """Scenario: A trainer cannot edit another trainer's template."""
    me = await user_repo.create(db_session, telegram_id=1, name="Me", role=UserRole.trainer)
    other = await user_repo.create(
        db_session, telegram_id=2, name="Other", role=UserRole.trainer
    )
    ex = await exercise_repo.create(
        db_session, trainer_id=other.id, name="X", unit=ExerciseUnit.reps
    )
    created = await http_client.post(
        "/api/workouts",
        json={"name": "T", "items": [{"exercise_id": ex.id, "sets": 1, "target_reps": 5}]},
        headers=init_data_header(2),
    )
    template_id = created.json()["id"]

    response = await http_client.put(
        f"/api/workouts/{template_id}",
        json={"name": "Hijack", "items": [{"exercise_id": ex.id, "sets": 1, "target_reps": 5}]},
        headers=init_data_header(1),
    )
    assert response.status_code == 404
    assert me.id != other.id


@pytest.mark.asyncio
async def test_list_templates_returns_own(http_client, db_session) -> None:
    coach = await user_repo.create(
        db_session, telegram_id=1, name="C", role=UserRole.trainer
    )
    e = await exercise_repo.create(
        db_session, trainer_id=coach.id, name="E", unit=ExerciseUnit.reps
    )
    await http_client.post(
        "/api/workouts",
        json={
            "name": "T1",
            "items": [{"exercise_id": e.id, "sets": 1, "target_reps": 10}],
        },
        headers=init_data_header(1),
    )

    response = await http_client.get("/api/workouts", headers=init_data_header(1))
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "T1"
