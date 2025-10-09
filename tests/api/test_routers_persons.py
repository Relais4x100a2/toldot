"""
Tests pour le router persons de l'API geneweb-py.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from geneweb_py.api.main import app
from geneweb_py.api.dependencies import get_genealogy_service
from geneweb_py.core.models import Person, Gender, AccessLevel, Date
from geneweb_py.api.services.genealogy_service import GenealogyService


@pytest.fixture
def mock_service():
    """Service mock pour les tests."""
    service = Mock(spec=GenealogyService)
    return service


@pytest.fixture
def client(mock_service):
    """Client de test FastAPI avec service mocké."""
    # Utiliser dependency_overrides au lieu de patch
    app.dependency_overrides[get_genealogy_service] = lambda: mock_service
    client = TestClient(app)
    yield client
    # Nettoyer après le test
    app.dependency_overrides.clear()


@pytest.fixture
def sample_person():
    """Personne d'exemple pour les tests."""
    person = Person(
        first_name="Jean",
        last_name="Dupont",
        gender=Gender.MALE,
        access_level=AccessLevel.PUBLIC,
        occurrence_number=1,
    )
    person.public_name = "Jean Dupont"
    person.birth_place = "Paris"
    person.death_place = "Lyon"
    person.burial_place = "Lyon"
    person.baptism_place = "Paris"
    person.notes = ["Note de test"]
    person.image_path = "test.jpg"
    return person


class TestCreatePerson:
    """Tests pour la création de personnes."""

    def test_create_person_success(self, client, mock_service, sample_person):
        """Test création d'une personne avec succès."""
        mock_service.create_person.return_value = sample_person

        response = client.post(
            "/api/v1/persons/",
            json={
                "first_name": "Jean",
                "surname": "Dupont",
                "sex": "male",
                "access_level": "public",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Personne créée avec succès"
        assert data["data"]["first_name"] == "Jean"
        assert data["data"]["surname"] == "Dupont"

    def test_create_person_with_optional_fields(self, client, mock_service):
        """Test création avec champs optionnels."""
        person = Person(
            first_name="Marie",
            last_name="Martin",
            gender=Gender.FEMALE,
            access_level=AccessLevel.PRIVATE,
            occurrence_number=1,
        )
        person.public_name = "Marie de Martin"
        person.image_path = "marie.jpg"

        mock_service.create_person.return_value = person

        response = client.post(
            "/api/v1/persons/",
            json={
                "first_name": "Marie",
                "surname": "Martin",
                "public_name": "Marie de Martin",
                "sex": "female",
                "access_level": "private",
                "image": "marie.jpg",
                "titles": [],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["first_name"] == "Marie"
        assert data["data"]["public_name"] == "Marie de Martin"

    def test_create_person_invalid_data(self, client):
        """Test création avec données invalides."""
        response = client.post(
            "/api/v1/persons/",
            json={
                "first_name": "",  # Nom vide invalide
                "surname": "Dupont",
                "sex": "male",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_create_person_service_error(self, client, mock_service):
        """Test erreur du service lors de la création."""
        mock_service.create_person.side_effect = Exception("Database error")

        response = client.post(
            "/api/v1/persons/",
            json={
                "first_name": "Jean",
                "surname": "Dupont",
                "sex": "male",
                "access_level": "public",
            },
        )

        assert response.status_code == 500


class TestGetPerson:
    """Tests pour la récupération d'une personne."""

    def test_get_person_success(self, client, mock_service, sample_person):
        """Test récupération d'une personne existante."""
        mock_service.get_person.return_value = sample_person

        response = client.get("/api/v1/persons/test_001")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Personne récupérée avec succès"
        assert data["data"]["id"] == "Dupont_Jean_1"
        assert data["data"]["first_name"] == "Jean"

    def test_get_person_not_found(self, client, mock_service):
        """Test récupération d'une personne inexistante."""
        mock_service.get_person.return_value = None

        response = client.get("/api/v1/persons/unknown")

        assert response.status_code == 404


class TestUpdatePerson:
    """Tests pour la mise à jour d'une personne."""

    def test_update_person_success(self, client, mock_service, sample_person):
        """Test mise à jour réussie."""
        sample_person.first_name = "Jean-Pierre"
        mock_service.update_person.return_value = sample_person

        response = client.put(
            "/api/v1/persons/test_001", json={"first_name": "Jean-Pierre"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Personne mise à jour avec succès"
        assert data["data"]["first_name"] == "Jean-Pierre"

    def test_update_person_not_found(self, client, mock_service):
        """Test mise à jour d'une personne inexistante."""
        mock_service.update_person.return_value = None

        response = client.put("/api/v1/persons/unknown", json={"first_name": "Jean"})

        assert response.status_code == 404

    def test_update_person_partial(self, client, mock_service, sample_person):
        """Test mise à jour partielle."""
        mock_service.update_person.return_value = sample_person

        response = client.put("/api/v1/persons/test_001", json={"public_name": "JD"})

        assert response.status_code == 200


class TestDeletePerson:
    """Tests pour la suppression d'une personne."""

    def test_delete_person_success(self, client, mock_service):
        """Test suppression réussie."""
        mock_service.delete_person.return_value = True

        response = client.delete("/api/v1/persons/test_001")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Personne supprimée avec succès"

    def test_delete_person_not_found(self, client, mock_service):
        """Test suppression d'une personne inexistante."""
        mock_service.delete_person.return_value = False

        response = client.delete("/api/v1/persons/unknown")

        assert response.status_code == 404


class TestListPersons:
    """Tests pour la liste paginée des personnes."""

    def test_list_persons_default(self, client, mock_service, sample_person):
        """Test liste avec paramètres par défaut."""
        mock_service.search_persons.return_value = ([sample_person], 1)

        response = client.get("/api/v1/persons/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1
        assert data["pagination"]["page"] == 1

    def test_list_persons_with_pagination(self, client, mock_service, sample_person):
        """Test liste avec pagination personnalisée."""
        mock_service.search_persons.return_value = ([sample_person], 10)

        response = client.get("/api/v1/persons/?page=2&size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["size"] == 5
        assert data["pagination"]["total"] == 10

    def test_list_persons_with_filters(self, client, mock_service, sample_person):
        """Test liste avec filtres."""
        mock_service.search_persons.return_value = ([sample_person], 1)

        response = client.get(
            "/api/v1/persons/?first_name=Jean&surname=Dupont"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    def test_list_persons_empty_result(self, client, mock_service):
        """Test liste sans résultats."""
        mock_service.search_persons.return_value = ([], 0)

        response = client.get("/api/v1/persons/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["pagination"]["total"] == 0


class TestGetPersonFamilies:
    """Tests pour la récupération des familles d'une personne."""

    def test_get_person_families_success(self, client, mock_service, sample_person):
        """Test récupération des familles."""
        mock_service.get_person.return_value = sample_person

        response = client.get("/api/v1/persons/test_001/families")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Familles récupérées avec succès"

    def test_get_person_families_not_found(self, client, mock_service):
        """Test familles d'une personne inexistante."""
        mock_service.get_person.return_value = None

        response = client.get("/api/v1/persons/unknown/families")

        assert response.status_code == 404


class TestGetPersonEvents:
    """Tests pour la récupération des événements d'une personne."""

    def test_get_person_events_success(self, client, mock_service, sample_person):
        """Test récupération des événements."""
        mock_service.get_person.return_value = sample_person

        response = client.get("/api/v1/persons/test_001/events")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Événements récupérés avec succès"

    def test_get_person_events_not_found(self, client, mock_service):
        """Test événements d'une personne inexistante."""
        mock_service.get_person.return_value = None

        response = client.get("/api/v1/persons/unknown/events")

        assert response.status_code == 404


class TestGetPersonStats:
    """Tests pour les statistiques des personnes."""

    def test_get_person_stats(self, client, mock_service):
        """Test récupération des statistiques."""
        mock_service.get_stats.return_value = {
            "total_persons": 100,
            "persons_by_sex": {"male": 60, "female": 40},
            "persons_by_access_level": {"public": 80, "private": 20},
            "persons_with_birth_date": 90,
            "persons_with_death_date": 30,
        }

        response = client.get("/api/v1/persons/stats/overview")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Statistiques récupérées avec succès"
        assert data["data"]["total"] == 100
        assert data["data"]["by_sex"]["male"] == 60
