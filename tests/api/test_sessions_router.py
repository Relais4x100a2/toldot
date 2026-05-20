"""Tests d'intégration pour le router /api/v1/sessions."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURE_GW = Path(__file__).parent.parent / "fixtures" / "simple_test.gw"


@pytest.fixture
def client():
    from geneweb_py.api.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c


def _upload_gw(client, path: Path = FIXTURE_GW):
    with open(path, "rb") as f:
        resp = client.post(
            "/api/v1/sessions",
            files={"file": ("simple_test.gw", f, "application/octet-stream")},
        )
    return resp


class TestCreateSession:
    def test_create_returns_201(self, client):
        resp = _upload_gw(client)
        assert resp.status_code == 201

    def test_create_returns_token_and_expiry(self, client):
        data = _upload_gw(client).json()
        assert "session_token" in data
        assert "expires_at" in data
        assert len(data["session_token"]) > 20

    def test_create_returns_stats(self, client):
        data = _upload_gw(client).json()
        assert "stats" in data
        assert "persons" in data["stats"]
        assert "families" in data["stats"]

    def test_create_cache_control_no_store(self, client):
        resp = _upload_gw(client)
        assert resp.headers.get("cache-control") == "no-store"

    def test_create_wrong_extension_returns_400(self, client, tmp_path):
        bad = tmp_path / "file.txt"
        bad.write_bytes(b"content")
        with open(bad, "rb") as f:
            resp = client.post(
                "/api/v1/sessions",
                files={"file": ("file.txt", f, "text/plain")},
            )
        assert resp.status_code == 400

    def test_create_invalid_mime_returns_415(self, client):
        with open(FIXTURE_GW, "rb") as f:
            resp = client.post(
                "/api/v1/sessions",
                files={"file": ("test.gw", f, "application/pdf")},
            )
        assert resp.status_code == 415


class TestDeleteSession:
    def test_delete_returns_204(self, client):
        token = _upload_gw(client).json()["session_token"]
        resp = client.delete(f"/api/v1/sessions/{token}")
        assert resp.status_code == 204

    def test_delete_unknown_returns_404(self, client):
        resp = client.delete("/api/v1/sessions/unknowntoken")
        assert resp.status_code == 404

    def test_token_invalid_after_delete(self, client):
        token = _upload_gw(client).json()["session_token"]
        client.delete(f"/api/v1/sessions/{token}")
        resp = client.get("/api/v1/persons/", headers={"X-Session-Token": token})
        assert resp.status_code == 401
