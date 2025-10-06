"""
Tests spécifiques pour le router persons.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from geneweb_py.api.main import app
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.family import Family


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Service mock pour les tests."""
    service = MagicMock(spec=GenealogyService)
    
    # Mock des données de test
    genealogy = Genealogy()
    
    # Créer des personnes
    person1 = Person(
        last_name="DUPONT",
        first_name="Jean",
        gender=Gender.MALE
    )
    person2 = Person(
        last_name="MARTIN",
        first_name="Marie",
        gender=Gender.FEMALE
    )
    genealogy.add_person(person1)
    genealogy.add_person(person2)
    
    # Créer une famille
    family = Family(
        family_id="test_family_1",
        husband_id=person1.unique_id,
        wife_id=person2.unique_id
    )
    genealogy.add_family(family)
    
    service.genealogy = genealogy
    service.get_person.return_value = person1
    service.get_persons.return_value = [person1, person2]
    service.create_person.return_value = person1
    service.update_person.return_value = person1
    service.delete_person.return_value = True
    service.get_person_families.return_value = [family]
    service.get_person_events.return_value = []
    
    return service


@pytest.fixture
def client_with_mock_service(mock_service):
    """Client avec service mock."""
    from geneweb_py.api.dependencies import get_genealogy_service
    from geneweb_py.api.main import app
    
    def get_mock_service():
        return mock_service
    
    app.dependency_overrides[get_genealogy_service] = get_mock_service
    
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()


class TestPersonsRouter:
    """Tests pour le router persons."""
    
    def test_get_persons(self, client_with_mock_service, mock_service):
        """Test récupération de toutes les personnes"""
        response = client_with_mock_service.get("/api/v1/persons")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "persons" in data["data"]
        assert len(data["data"]["persons"]) == 2
    
    def test_get_persons_with_pagination(self, client_with_mock_service, mock_service):
        """Test récupération avec pagination"""
        response = client_with_mock_service.get("/api/v1/persons?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "persons" in data["data"]
    
    def test_get_persons_with_filters(self, client_with_mock_service, mock_service):
        """Test récupération avec filtres"""
        response = client_with_mock_service.get("/api/v1/persons?gender=male")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_person_by_id(self, client_with_mock_service, mock_service):
        """Test récupération d'une personne par ID"""
        person_id = "test_person_id"
        mock_service.get_person.return_value = list(mock_service.genealogy.persons.values())[0]
        
        response = client_with_mock_service.get(f"/api/v1/persons/{person_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "person" in data["data"]
    
    def test_get_person_not_found(self, client_with_mock_service, mock_service):
        """Test récupération d'une personne inexistante"""
        mock_service.get_person.return_value = None
        
        response = client_with_mock_service.get("/api/v1/persons/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error"] is True
    
    def test_create_person(self, client_with_mock_service, mock_service):
        """Test création d'une personne"""
        person_data = {
            "last_name": "DURAND",
            "first_name": "Pierre",
            "gender": "male"
        }
        
        response = client_with_mock_service.post("/api/v1/persons", json=person_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "person" in data["data"]
    
    def test_create_person_invalid_data(self, client_with_mock_service):
        """Test création avec données invalides"""
        person_data = {
            "last_name": "DURAND",
            "gender": "invalid_gender"
        }
        
        response = client_with_mock_service.post("/api/v1/persons", json=person_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_update_person(self, client_with_mock_service, mock_service):
        """Test mise à jour d'une personne"""
        person_id = "test_person_id"
        person_data = {
            "first_name": "Jean-Pierre",
            "notes": "Mise à jour"
        }
        
        response = client_with_mock_service.put(f"/api/v1/persons/{person_id}", json=person_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "person" in data["data"]
    
    def test_update_person_not_found(self, client_with_mock_service, mock_service):
        """Test mise à jour d'une personne inexistante"""
        mock_service.update_person.return_value = None
        
        person_data = {"first_name": "Jean-Pierre"}
        response = client_with_mock_service.put("/api/v1/persons/nonexistent", json=person_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error"] is True
    
    def test_delete_person(self, client_with_mock_service, mock_service):
        """Test suppression d'une personne"""
        person_id = "test_person_id"
        
        response = client_with_mock_service.delete(f"/api/v1/persons/{person_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "supprimée" in data["message"]
    
    def test_delete_person_not_found(self, client_with_mock_service, mock_service):
        """Test suppression d'une personne inexistante"""
        mock_service.delete_person.return_value = False
        
        response = client_with_mock_service.delete("/api/v1/persons/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error"] is True
    
    def test_get_person_families(self, client_with_mock_service, mock_service):
        """Test récupération des familles d'une personne"""
        person_id = "test_person_id"
        
        response = client_with_mock_service.get(f"/api/v1/persons/{person_id}/families")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "families" in data["data"]
    
    def test_get_person_events(self, client_with_mock_service, mock_service):
        """Test récupération des événements d'une personne"""
        person_id = "test_person_id"
        
        response = client_with_mock_service.get(f"/api/v1/persons/{person_id}/events")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]
    
    def test_search_persons(self, client_with_mock_service, mock_service):
        """Test recherche de personnes"""
        # Mock de la recherche
        mock_service.search_persons.return_value = [list(mock_service.genealogy.persons.values())[0]]
        
        response = client_with_mock_service.get("/api/v1/persons/search?query=DUPONT")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data["data"]
    
    def test_search_persons_no_query(self, client_with_mock_service):
        """Test recherche sans query"""
        response = client_with_mock_service.get("/api/v1/persons/search")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["error"] is True
