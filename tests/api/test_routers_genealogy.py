"""
Tests pour le router genealogy de l'API geneweb-py.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from geneweb_py.api.main import app
from geneweb_py.core.models import Genealogy
from geneweb_py.api.services.genealogy_service import GenealogyService


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Service mock pour les tests."""
    service = Mock(spec=GenealogyService)
    return service


@pytest.fixture
def sample_genealogy():
    """Généalogie d'exemple pour les tests."""
    return Genealogy()


class TestImportGenealogy:
    """Tests pour l'import de fichiers généalogiques."""

    def test_import_gw_file_success(self, client, mock_service, sample_genealogy):
        """Test import d'un fichier .gw."""
        mock_service.load_from_file.return_value = sample_genealogy
        mock_service.get_stats.return_value = {
            "total_persons": 10,
            "total_families": 5,
        }

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
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

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            files = {"file": ("test.gw", b"invalid content", "text/plain")}
            response = client.post("/api/v1/genealogy/import", files=files)

        assert response.status_code == 500


class TestExportGenealogy:
    """Tests pour l'export de généalogies."""

    def test_export_gedcom_success(self, client, mock_service, sample_genealogy):
        """Test export au format GEDCOM."""
        mock_service.get_genealogy.return_value = sample_genealogy

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            with patch("geneweb_py.api.routers.genealogy.GEDCOMExporter") as mock_exporter:
                mock_instance = MagicMock()
                mock_exporter.return_value = mock_instance
                mock_instance.export_to_file.return_value = None

                response = client.get("/api/v1/genealogy/export?format=gedcom")

        assert response.status_code == 200

    def test_export_json_success(self, client, mock_service, sample_genealogy):
        """Test export au format JSON."""
        mock_service.get_genealogy.return_value = sample_genealogy

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            with patch("geneweb_py.api.routers.genealogy.JSONExporter") as mock_exporter:
                mock_instance = MagicMock()
                mock_exporter.return_value = mock_instance
                mock_instance.export_to_file.return_value = None

                response = client.get("/api/v1/genealogy/export?format=json")

        assert response.status_code == 200

    def test_export_xml_success(self, client, mock_service, sample_genealogy):
        """Test export au format XML."""
        mock_service.get_genealogy.return_value = sample_genealogy

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            with patch("geneweb_py.api.routers.genealogy.XMLExporter") as mock_exporter:
                mock_instance = MagicMock()
                mock_exporter.return_value = mock_instance
                mock_instance.export_to_file.return_value = None

                response = client.get("/api/v1/genealogy/export?format=xml")

        assert response.status_code == 200

    def test_export_invalid_format(self, client, mock_service, sample_genealogy):
        """Test export avec format invalide."""
        mock_service.get_genealogy.return_value = sample_genealogy

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            response = client.get("/api/v1/genealogy/export?format=invalid")

        assert response.status_code == 400


class TestGetStats:
    """Tests pour les statistiques."""

    def test_get_stats_success(self, client, mock_service):
        """Test récupération des statistiques."""
        mock_service.get_stats.return_value = {
            "total_persons": 100,
            "total_families": 50,
            "persons_by_sex": {"male": 60, "female": 40},
            "families_by_status": {"married": 40, "divorced": 10},
        }

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            response = client.get("/api/v1/genealogy/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_persons"] == 100
        assert data["total_families"] == 50


class TestSearchGlobal:
    """Tests pour la recherche globale."""

    def test_search_success(self, client, mock_service):
        """Test recherche avec résultats."""
        mock_service.search_global.return_value = {
            "persons": [],
            "families": [],
            "events": [],
        }

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            response = client.get("/api/v1/genealogy/search?query=Dupont")

        assert response.status_code == 200

    def test_search_missing_query(self, client):
        """Test recherche sans query."""
        response = client.get("/api/v1/genealogy/search")

        assert response.status_code == 422


class TestHealthCheck:
    """Tests pour le health check."""

    def test_health_check_success(self, client, mock_service):
        """Test health check avec succès."""
        mock_service.health_check.return_value = True

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            response = client.get("/api/v1/genealogy/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_unhealthy(self, client, mock_service):
        """Test health check avec échec."""
        mock_service.health_check.return_value = False

        with patch(
            "geneweb_py.api.routers.genealogy.get_genealogy_service",
            return_value=mock_service,
        ):
            response = client.get("/api/v1/genealogy/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"

