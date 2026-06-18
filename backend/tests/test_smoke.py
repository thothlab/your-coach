import os

from fastapi.testclient import TestClient

from trainbeat.main import app


def test_healthz() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["env"] == os.environ["APP_ENV"]
