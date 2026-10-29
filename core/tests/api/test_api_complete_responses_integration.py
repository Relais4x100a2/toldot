"""
Tests d'intégration API : réponses enrichies (dates, listes, stats par siècle).
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from geneweb_py.api.dependencies import get_session_service
from geneweb_py.api.main import app
from geneweb_py.api.models.event import PersonalEventCreateSchema
from geneweb_py.api.services.genealogy_service import GenealogyService

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def integration_client():
    """Client avec service isolé et fichier .gw chargé."""
    service = GeneWebServiceForTest()
    service.load_from_file(str(FIXTURES / "simple_family.gw"))
    app.dependency_overrides[get_session_service] = lambda: service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class GeneWebServiceForTest(GenealogyService):
    """Sous-classe pour éviter la mutation du singleton global dans les tests."""


class TestGenealogyStatsCenturies:
    """Statistiques /genealogy/stats incluent la répartition par siècle."""

    def test_stats_include_century_breakdowns(self, integration_client):
        response = integration_client.get("/api/v1/genealogy/stats")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "persons_by_birth_century" in data
        assert "families_by_marriage_century" in data
        assert "events_by_century" in data
        assert isinstance(data["persons_by_birth_century"], dict)


class TestPersonRelatedAndLists:
    """Personnes : familles liées, conjoint, événements."""

    def test_get_person_includes_families_and_related(self, integration_client):
        response = integration_client.get("/api/v1/persons/CORNO_Jean_0")
        assert response.status_code == 200
        body = response.json()["data"]
        assert body["families"] == ["FAM_001"]
        assert body["related_families"] == []


class TestFamilyChildrenPayload:
    """Famille : enfants avec détails personne."""

    def test_family_children_not_empty(self, integration_client):
        response = integration_client.get("/api/v1/families/FAM_001/children")
        assert response.status_code == 200
        kids = response.json()["data"]
        assert isinstance(kids, list)
        assert len(kids) >= 2
        assert all("person_id" in row and "person" in row for row in kids)
        jean = next(k for k in kids if k["person_id"] == "CORNO_Jean_0")
        assert jean["person"] is not None
        assert jean["person"]["first_name"] == "Jean"


class TestPersonSubresources:
    """Sous-routes /families et /events retournent des données réelles."""

    def test_person_families_returns_family_objects(self, integration_client):
        response = integration_client.get("/api/v1/persons/CORNO_Joseph_0/families")
        assert response.status_code == 200
        fams = response.json()["data"]
        assert len(fams) == 1
        assert fams[0]["id"] == "FAM_001"
        assert len(fams[0]["children"]) >= 1

    def test_person_events_after_create(self, integration_client):
        service = GeneWebServiceForTest()
        service.load_from_file(str(FIXTURES / "simple_family.gw"))
        app.dependency_overrides[get_session_service] = lambda: service
        client = TestClient(app)
        try:
            service.create_personal_event(
                PersonalEventCreateSchema(
                    person_id="CORNO_Joseph_0",
                    event_type="birth",
                    date="15/03/1955",
                    place="Paris",
                )
            )
            res = client.get("/api/v1/persons/CORNO_Joseph_0/events")
            assert res.status_code == 200
            evs = res.json()["data"]
            assert len(evs) == 1
            assert evs[0]["date"] == "15/03/1955"
            assert evs[0]["place"] == "Paris"
        finally:
            app.dependency_overrides.clear()


class TestValidateEndpoint:
    """Validation de cohérence renvoie le typique du service."""

    def test_validate_strict_false(self, integration_client):
        response = integration_client.post("/api/v1/genealogy/validate")
        assert response.status_code == 200
        payload = response.json()["data"]
        assert "is_valid" in payload
        assert "errors" in payload
        assert isinstance(payload["errors"], list)
