"""
Tests pour le router genealogy de l'API geneweb-py.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from geneweb_py.api.dependencies import get_session_service
from geneweb_py.api.main import app
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.models import Genealogy


@pytest.fixture
def mock_service():
    """Service mock pour les tests."""
    service = Mock(spec=GenealogyService)
    return service


@pytest.fixture
def client(mock_service):
    """Client de test FastAPI avec service mocké."""
    app.dependency_overrides[get_session_service] = lambda: mock_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_genealogy():
    """Généalogie d'exemple pour les tests."""
    return Genealogy()


class TestGetStats:
    """Tests pour les statistiques."""

    def test_get_stats_success(self, client, mock_service):
        """Test récupération des statistiques."""
        from datetime import datetime

        mock_service.get_stats.return_value = {
            "total_persons": 100,
            "total_families": 50,
            "total_events": 80,
            "persons_by_sex": {"male": 60, "female": 40},
            "families_by_status": {"married": 40, "divorced": 10},
            "metadata": {
                "source_file": "test.gw",
                "encoding": "utf-8",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "version": "1.0",
            },
            "persons_by_access_level": {"public": 80, "private": 20},
            "events_by_type": {"birth": 40, "death": 30},
            "average_children_per_family": 2.5,
        }

        response = client.get("/api/v1/genealogy/stats")

        assert response.status_code == 200
        data = response.json()
        # Les données sont wrappées dans SuccessResponse
        assert data["data"]["total_persons"] == 100
        assert data["data"]["total_families"] == 50


class TestValidateGenealogy:
    """Tests pour la validation de cohérence."""

    def test_validate_returns_service_payload(self, client, mock_service):
        """La route délègue au service et enveloppe dans SuccessResponse."""
        mock_service.validate_genealogy.return_value = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": [],
        }
        response = client.post("/api/v1/genealogy/validate")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["is_valid"] is True
        assert "aucune erreur" in body["message"]
        mock_service.validate_genealogy.assert_called_once_with(strict=False)

    def test_validate_strict_query_propagated(self, client, mock_service):
        """Le paramètre query strict est transmis au service."""
        mock_service.validate_genealogy.return_value = {
            "is_valid": False,
            "warnings": [],
            "errors": [{"type": "GeneWebValidationError", "message": "x"}],
            "suggestions": [],
        }
        response = client.post("/api/v1/genealogy/validate?strict=true")
        assert response.status_code == 200
        body = response.json()
        assert "présente des erreurs" in body["message"]
        mock_service.validate_genealogy.assert_called_once_with(strict=True)


class TestSearchGlobal:
    """Tests pour la recherche globale."""

    def test_search_missing_query(self, client):
        """Test recherche sans query."""
        response = client.get("/api/v1/genealogy/search")

        assert response.status_code == 422


class TestHealthCheck:
    """Tests pour le health check."""

    def test_health_check_success(self, client):
        """Test health check retourne 200."""
        response = client.get("/api/v1/genealogy/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
