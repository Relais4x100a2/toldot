"""
Tests spécifiques pour le router events.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from geneweb_py.api.main import app
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
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
    
    # Ajouter un événement
    event = Event(
        event_type=EventType.BIRTH,
        date=Date(day=15, month=6, year=1990),
        place="Paris",
        person_id=person.unique_id
    )
    person.events.append(event)
    
    service.genealogy = genealogy
    service.get_event.return_value = event
    service.search_events.return_value = ([event], 1)
    service.create_personal_event.return_value = event
    service.create_family_event.return_value = event
    service.update_event.return_value = event
    service.delete_event.return_value = True
    
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


class TestEventsRouter:
    """Tests pour le router events."""
    
    def test_get_events(self, client_with_mock_service, mock_service):
        """Test récupération de tous les événements"""
        response = client_with_mock_service.get("/api/v1/events")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) == 1
    
    def test_get_events_with_pagination(self, client_with_mock_service, mock_service):
        """Test récupération avec pagination"""
        response = client_with_mock_service.get("/api/v1/events?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]
    
    def test_get_events_with_filters(self, client_with_mock_service, mock_service):
        """Test récupération avec filtres"""
        response = client_with_mock_service.get("/api/v1/events?event_type=birth")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_event_by_id(self, client_with_mock_service, mock_service):
        """Test récupération d'un événement par ID"""
        event_id = "test_event_id"
        mock_service.get_event.return_value = mock_service.genealogy.persons[list(mock_service.genealogy.persons.keys())[0]].events[0]
        
        response = client_with_mock_service.get(f"/api/v1/events/{event_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event" in data["data"]
    
    def test_get_event_not_found(self, client_with_mock_service, mock_service):
        """Test récupération d'un événement inexistant"""
        mock_service.get_event.return_value = None
        
        response = client_with_mock_service.get("/api/v1/events/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error"] is True
    
    def test_create_event(self, client_with_mock_service, mock_service):
        """Test création d'un événement"""
        event_data = {
            "event_type": "birth",
            "date": "15/06/1990",
            "place": "Paris",
            "person_id": "test_person_id"
        }
        
        response = client_with_mock_service.post("/api/v1/events", json=event_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "event" in data["data"]
    
    def test_create_event_invalid_data(self, client_with_mock_service):
        """Test création avec données invalides"""
        event_data = {
            "event_type": "invalid_type",
            "date": "invalid_date"
        }
        
        response = client_with_mock_service.post("/api/v1/events", json=event_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_update_event(self, client_with_mock_service, mock_service):
        """Test mise à jour d'un événement"""
        event_id = "test_event_id"
        event_data = {
            "place": "Lyon",
            "notes": "Mise à jour"
        }
        
        response = client_with_mock_service.put(f"/api/v1/events/{event_id}", json=event_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event" in data["data"]
    
    def test_update_event_not_found(self, client_with_mock_service, mock_service):
        """Test mise à jour d'un événement inexistant"""
        mock_service.update_event.return_value = None
        
        event_data = {"place": "Lyon"}
        response = client_with_mock_service.put("/api/v1/events/nonexistent", json=event_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error"] is True
    
    def test_delete_event(self, client_with_mock_service, mock_service):
        """Test suppression d'un événement"""
        event_id = "test_event_id"
        
        response = client_with_mock_service.delete(f"/api/v1/events/{event_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "supprimé" in data["message"]
    
    def test_delete_event_not_found(self, client_with_mock_service, mock_service):
        """Test suppression d'un événement inexistant"""
        mock_service.delete_event.return_value = False
        
        response = client_with_mock_service.delete("/api/v1/events/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error"] is True
    
    def test_get_events_by_person(self, client_with_mock_service, mock_service):
        """Test récupération des événements d'une personne"""
        person_id = "test_person_id"
        
        response = client_with_mock_service.get(f"/api/v1/events/person/{person_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]
    
    def test_get_events_by_family(self, client_with_mock_service, mock_service):
        """Test récupération des événements d'une famille"""
        family_id = "test_family_id"
        
        response = client_with_mock_service.get(f"/api/v1/events/family/{family_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]
