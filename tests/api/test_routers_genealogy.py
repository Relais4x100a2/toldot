"""
Tests pour le router genealogy de l'API geneweb-py.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from geneweb_py.api.dependencies import get_genealogy_service
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
    app.dependency_overrides[get_genealogy_service] = lambda: mock_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_genealogy():
    """Généalogie d'exemple pour les tests."""
    return Genealogy()


class TestImportGenealogy:
    """Tests pour l'import de fichiers généalogiques."""

    def test_import_wrapped_filename_uses_basename_only(
        self, client, mock_service, sample_genealogy
    ):
        """Le nom fourni par le client ne doit pas contenir de chemin (traversal)."""
        mock_service.load_from_file.return_value = sample_genealogy
        mock_service.get_stats.return_value = {
            "total_persons": 1,
            "total_families": 0,
        }
        files = {
            "file": ("../../etc/passwd.gw", b"x", "text/plain"),
        }
        response = client.post("/api/v1/genealogy/import", files=files)
        assert response.status_code == 200
        assert response.json()["data"]["filename"] == "passwd.gw"

    def test_import_rejects_oversized_body(
        self, client, mock_service, sample_genealogy, monkeypatch
    ):
        """Le corps de l'upload est refusé au-delà de MAX_UPLOAD_BYTES."""
        monkeypatch.setattr(
            "geneweb_py.api.routers.genealogy.MAX_UPLOAD_BYTES",
            10,
        )
        mock_service.load_from_file.return_value = sample_genealogy
        mock_service.get_stats.return_value = {
            "total_persons": 0,
            "total_families": 0,
        }
        files = {"file": ("big.gw", b"x" * 20, "text/plain")}
        response = client.post("/api/v1/genealogy/import", files=files)
        assert response.status_code == 413

    def test_import_gw_file_success(self, client, mock_service, sample_genealogy):
        """Test import d'un fichier .gw."""
        mock_service.load_from_file.return_value = sample_genealogy
        mock_service.get_stats.return_value = {
            "total_persons": 10,
            "total_families": 5,
        }

        files = {"file": ("test.gw", b"test content", "text/plain")}
        response = client.post("/api/v1/genealogy/import", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "importé avec succès" in data["message"]

    def test_import_invalid_extension(self, client):
        """Test import avec extension invalide."""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = client.post("/api/v1/genealogy/import", files=files)

        assert response.status_code == 400

    def test_import_error(self, client, mock_service):
        """Test erreur lors de l'import."""
        mock_service.load_from_file.side_effect = Exception("Parse error")

        files = {"file": ("test.gw", b"invalid content", "text/plain")}
        response = client.post("/api/v1/genealogy/import", files=files)

        body = response.json()
        assert response.status_code == 500
        assert body.get("message") == (
            "Une erreur interne s'est produite. Réessayez plus tard."
        )


class TestExportGenealogy:
    """Tests pour l'export de généalogies."""

    @pytest.mark.skip(
        reason="Export nécessite une implémentation complète avec fichiers temporaires"
    )
    def test_export_gedcom_success(self, client, mock_service, sample_genealogy):
        """Test export au format GEDCOM."""
        pass

    @pytest.mark.skip(
        reason="Export nécessite une implémentation complète avec fichiers temporaires"
    )
    def test_export_json_success(self, client, mock_service, sample_genealogy):
        """Test export au format JSON."""
        pass

    @pytest.mark.skip(
        reason="Export nécessite une implémentation complète avec fichiers temporaires"
    )
    def test_export_xml_success(self, client, mock_service, sample_genealogy):
        """Test export au format XML."""
        pass

    @pytest.mark.skip(reason="Route export nécessite implémentation complète")
    def test_export_invalid_format(self, client, mock_service, sample_genealogy):
        """Test export avec format invalide."""
        pass


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

    @pytest.mark.skip(reason="search_global non implémenté dans le service")
    def test_search_success(self, client, mock_service):
        """Test recherche avec résultats."""
        pass

    def test_search_missing_query(self, client):
        """Test recherche sans query."""
        response = client.get("/api/v1/genealogy/search")

        assert response.status_code == 422


class TestHealthCheck:
    """Tests pour le health check."""

    @pytest.mark.skip(reason="health_check non implémenté dans le service")
    def test_health_check_success(self, client, mock_service):
        """Test health check avec succès."""
        pass

    @pytest.mark.skip(reason="health_check non implémenté dans le service")
    def test_health_check_unhealthy(self, client, mock_service):
        """Test health check avec échec."""
        pass
