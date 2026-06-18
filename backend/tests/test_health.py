import pytest


@pytest.mark.asyncio
async def test_healthz_returns_ok(http_client) -> None:
    response = await http_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz_returns_ok_when_db_reachable(http_client) -> None:
    response = await http_client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
