"""
Tests simples pour le router events.py - objets Event de base
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from geneweb_py.api.main import app
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.family import Family
from geneweb_py.core.event import Event, EventType
from geneweb_py.core.date import Date


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
    
    # Mock des événements
    event1 = Event(
        event_type=EventType.BIRTH,
        date=Date(day=15, month=6, year=1990),
        place="Paris"
    )
    
    event2 = Event(
        event_type=EventType.MARRIAGE,
        date=Date(day=20, month=8, year=2015),
        place="Lyon"
    )
    
    service.genealogy = genealogy
    service.get_event.return_value = event1
    service.create_personal_event.return_value = event1
    service.create_family_event.return_value = event2
    service.update_event.return_value = event1
    service.delete_event.return_value = True
    service.search_events.return_value = ([event1, event2], 2)
    
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


class TestEventsRouterSimple:
    """Tests simples pour le router events."""
    
    def test_get_events_success(self, client_with_mock_service, mock_service):
        """Test récupération de la liste des événements - succès"""
        response = client_with_mock_service.get("/api/v1/events")
        
        assert response.status_code == 200
        data = response.json()
        # Vérifier que la réponse contient des données
        assert "items" in data or "data" in data
        # Le router utilise search_events avec des paramètres vides
        mock_service.search_events.assert_called_once()
    
    def test_get_event_success(self, client_with_mock_service, mock_service):
        """Test récupération d'un événement - succès"""
        response = client_with_mock_service.get("/api/v1/events/test_event_1")
        
        assert response.status_code == 200
        data = response.json()
        # Vérifier que la réponse contient des données
        assert "data" in data or "items" in data
    
    def test_get_event_not_found(self, client_with_mock_service, mock_service):
        """Test récupération d'un événement - non trouvé"""
        mock_service.get_event.return_value = None
        
        response = client_with_mock_service.get("/api/v1/events/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_create_personal_event_success(self, client_with_mock_service, mock_service):
        """Test création d'un événement personnel - succès"""
        event_data = {
            "event_type": "birth",
            "date": "1990-06-15",
            "place": "Paris",
            "person_id": "DUPONT_Jean_1"
        }
        
        response = client_with_mock_service.post("/api/v1/events/personal", json=event_data)
        
        assert response.status_code == 201
        data = response.json()
        # Vérifier que la réponse contient des données
        assert "data" in data or "items" in data
    
    def test_create_personal_event_invalid(self, client_with_mock_service):
        """Test création d'un événement personnel - données invalides"""
        event_data = {}  # Données manquantes
        
        response = client_with_mock_service.post("/api/v1/events/personal", json=event_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_create_family_event_success(self, client_with_mock_service, mock_service):
        """Test création d'un événement familial - succès"""
        event_data = {
            "event_type": "marriage",
            "date": "2015-08-20",
            "place": "Lyon",
            "family_id": "test_family_1"
        }
        
        response = client_with_mock_service.post("/api/v1/events/family", json=event_data)
        
        assert response.status_code == 201
        data = response.json()
        # Vérifier que la réponse contient des données
        assert "data" in data or "items" in data
    
    def test_create_family_event_invalid(self, client_with_mock_service):
        """Test création d'un événement familial - données invalides"""
        event_data = {}  # Données manquantes
        
        response = client_with_mock_service.post("/api/v1/events/family", json=event_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_update_event_success(self, client_with_mock_service, mock_service):
        """Test mise à jour d'un événement - succès"""
        update_data = {
            "place": "Marseille"
        }
        
        response = client_with_mock_service.put("/api/v1/events/test_event_1", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "items" in data
    
    def test_update_event_not_found(self, client_with_mock_service, mock_service):
        """Test mise à jour d'un événement - non trouvé"""
        mock_service.update_event.return_value = None
        
        update_data = {
            "place": "Marseille"
        }
        
        response = client_with_mock_service.put("/api/v1/events/nonexistent", json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_delete_event_success(self, client_with_mock_service, mock_service):
        """Test suppression d'un événement - succès"""
        response = client_with_mock_service.delete("/api/v1/events/test_event_1")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "data" in data
    
    def test_delete_event_not_found(self, client_with_mock_service, mock_service):
        """Test suppression d'un événement - non trouvé"""
        mock_service.delete_event.return_value = False
        
        response = client_with_mock_service.delete("/api/v1/events/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
