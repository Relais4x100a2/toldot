"""
Tests simples pour le router persons.py - méthodes existantes uniquement
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
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
    person = Person(
        last_name="DUPONT",
        first_name="Jean",
        gender=Gender.MALE
    )
    genealogy.add_person(person)
    
    family = Family(
        family_id="test_family_1",
        husband_id=person.unique_id,
        wife_id=None
    )
    genealogy.add_family(family)
    
    service.genealogy = genealogy
    service.get_person.return_value = person
    service.create_person.return_value = person
    service.update_person.return_value = person
    service.delete_person.return_value = True
    service.search_persons.return_value = ([person], 1)
    
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


class TestPersonsRouterSimple:
    """Tests simples pour le router persons."""
    
    def test_get_persons_success(self, client_with_mock_service, mock_service):
        """Test récupération de la liste des personnes - succès"""
        response = client_with_mock_service.get("/api/v1/persons")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # Le router utilise search_persons avec des paramètres vides
        mock_service.search_persons.assert_called_once()
    
    def test_get_person_success(self, client_with_mock_service, mock_service):
        """Test récupération d'une personne - succès"""
        response = client_with_mock_service.get("/api/v1/persons/DUPONT_Jean_1")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["last_name"] == "DUPONT"
    
    def test_get_person_not_found(self, client_with_mock_service, mock_service):
        """Test récupération d'une personne - non trouvée"""
        mock_service.get_person.return_value = None
        
        response = client_with_mock_service.get("/api/v1/persons/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_create_person_success(self, client_with_mock_service, mock_service):
        """Test création d'une personne - succès"""
        person_data = {
            "surname": "MARTIN",
            "first_name": "Marie",
            "sex": "female"
        }
        
        response = client_with_mock_service.post("/api/v1/persons", json=person_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert data["data"]["last_name"] == "MARTIN"
    
    def test_create_person_invalid(self, client_with_mock_service):
        """Test création d'une personne - données invalides"""
        person_data = {}  # Données manquantes
        
        response = client_with_mock_service.post("/api/v1/persons", json=person_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_update_person_success(self, client_with_mock_service, mock_service):
        """Test mise à jour d'une personne - succès"""
        update_data = {
            "first_name": "Jean-Pierre"
        }
        
        response = client_with_mock_service.put("/api/v1/persons/DUPONT_Jean_1", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_update_person_not_found(self, client_with_mock_service, mock_service):
        """Test mise à jour d'une personne - non trouvée"""
        mock_service.update_person.return_value = None
        
        update_data = {
            "first_name": "Jean-Pierre"
        }
        
        response = client_with_mock_service.put("/api/v1/persons/nonexistent", json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_delete_person_success(self, client_with_mock_service, mock_service):
        """Test suppression d'une personne - succès"""
        response = client_with_mock_service.delete("/api/v1/persons/DUPONT_Jean_1")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_delete_person_not_found(self, client_with_mock_service, mock_service):
        """Test suppression d'une personne - non trouvée"""
        mock_service.delete_person.return_value = False
        
        response = client_with_mock_service.delete("/api/v1/persons/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data
