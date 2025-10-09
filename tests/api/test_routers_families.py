"""
Tests pour le router families de l'API geneweb-py.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from geneweb_py.api.main import app
from geneweb_py.api.dependencies import get_genealogy_service
from geneweb_py.core.models import Family, MarriageStatus
from geneweb_py.api.services.genealogy_service import GenealogyService


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
def sample_family():
    """Famille d'exemple pour les tests."""
    family = Family(
        family_id="fam_001",
        husband_id="h001",
        wife_id="w001",
        marriage_status=MarriageStatus.MARRIED,
    )
    family.children = ["c001", "c002"]
    family.comments = ["Commentaire famille"]
    family.family_source = "Source famille"
    return family


class TestCreateFamily:
    """Tests pour la création de familles."""

    def test_create_family_success(self, client, mock_service, sample_family):
        """Test création d'une famille avec succès."""
        mock_service.create_family.return_value = sample_family

        response = client.post(
            "/api/v1/families/",
            json={
                "husband_id": "h001",
                "wife_id": "w001",
                "marriage_status": "married",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Famille créée avec succès"
        assert data["data"]["husband_id"] == "h001"
        assert data["data"]["wife_id"] == "w001"

    def test_create_family_error(self, client, mock_service):
        """Test erreur lors de la création."""
        mock_service.create_family.side_effect = Exception("Database error")

        response = client.post(
            "/api/v1/families/",
            json={
                "husband_id": "h001",
                "wife_id": "w001",
                "marriage_status": "married",
            },
        )

        assert response.status_code == 500


class TestGetFamily:
    """Tests pour la récupération d'une famille."""

    def test_get_family_success(self, client, mock_service, sample_family):
        """Test récupération d'une famille existante."""
        mock_service.get_family.return_value = sample_family

        response = client.get("/api/v1/families/fam_001")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Famille récupérée avec succès"
        assert data["data"]["id"] == "fam_001"

    def test_get_family_not_found(self, client, mock_service):
        """Test récupération d'une famille inexistante."""
        mock_service.get_family.return_value = None

        response = client.get("/api/v1/families/unknown")

        assert response.status_code == 404


class TestUpdateFamily:
    """Tests pour la mise à jour d'une famille."""

    def test_update_family_success(self, client, mock_service, sample_family):
        """Test mise à jour réussie."""
        mock_service.update_family.return_value = sample_family

        response = client.put(
            "/api/v1/families/fam_001", json={"marriage_status": "divorced"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Famille mise à jour avec succès"

    def test_update_family_not_found(self, client, mock_service):
        """Test mise à jour d'une famille inexistante."""
        mock_service.update_family.return_value = None

        response = client.put("/api/v1/families/unknown", json={"marriage_status": "married"})

        assert response.status_code == 404


class TestDeleteFamily:
    """Tests pour la suppression d'une famille."""

    def test_delete_family_success(self, client, mock_service):
        """Test suppression réussie."""
        mock_service.delete_family.return_value = True

        response = client.delete("/api/v1/families/fam_001")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Famille supprimée avec succès"

    def test_delete_family_not_found(self, client, mock_service):
        """Test suppression d'une famille inexistante."""
        mock_service.delete_family.return_value = False

        response = client.delete("/api/v1/families/unknown")

        assert response.status_code == 404


class TestListFamilies:
    """Tests pour la liste paginée des familles."""

    def test_list_families_default(self, client, mock_service, sample_family):
        """Test liste avec paramètres par défaut."""
        mock_service.search_families.return_value = ([sample_family], 1)

        response = client.get("/api/v1/families/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1

    def test_list_families_with_filters(self, client, mock_service, sample_family):
        """Test liste avec filtres."""
        mock_service.search_families.return_value = ([sample_family], 1)

        response = client.get(
            "/api/v1/families/?husband_id=h001&wife_id=w001&has_children=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    def test_list_families_pagination(self, client, mock_service, sample_family):
        """Test pagination."""
        mock_service.search_families.return_value = ([sample_family], 10)

        response = client.get("/api/v1/families/?page=2&size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["size"] == 5


class TestGetFamilyChildren:
    """Tests pour la récupération des enfants d'une famille."""

    def test_get_family_children_success(self, client, mock_service, sample_family):
        """Test récupération des enfants."""
        mock_service.get_family.return_value = sample_family

        response = client.get("/api/v1/families/fam_001/children")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Enfants récupérés avec succès"

    def test_get_family_children_not_found(self, client, mock_service):
        """Test enfants d'une famille inexistante."""
        mock_service.get_family.return_value = None

        response = client.get("/api/v1/families/unknown/children")

        assert response.status_code == 404


class TestGetFamilyEvents:
    """Tests pour la récupération des événements d'une famille."""

    def test_get_family_events_success(self, client, mock_service, sample_family):
        """Test récupération des événements."""
        sample_family.events = []
        mock_service.get_family.return_value = sample_family

        response = client.get("/api/v1/families/fam_001/events")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Événements récupérés avec succès"

    def test_get_family_events_not_found(self, client, mock_service):
        """Test événements d'une famille inexistante."""
        mock_service.get_family.return_value = None

        response = client.get("/api/v1/families/unknown/events")

        assert response.status_code == 404


class TestGetFamilyStats:
    """Tests pour les statistiques des familles."""

    def test_get_family_stats(self, client, mock_service):
        """Test récupération des statistiques."""
        mock_service.get_stats.return_value = {
            "total_families": 50,
            "families_by_status": {"married": 40, "divorced": 10},
            "average_children_per_family": 2.5,
            "families_with_children": 45,
        }

        response = client.get("/api/v1/families/stats/overview")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Statistiques récupérées avec succès"
        assert data["data"]["total"] == 50
