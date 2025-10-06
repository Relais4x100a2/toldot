"""
Tests simples pour améliorer la couverture de code des API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from geneweb_py.api.main import app
from geneweb_py.api.services.genealogy_service import GenealogyService


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Service mock simple pour les tests."""
    service = MagicMock(spec=GenealogyService)
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


class TestSimpleCoverage:
    """Tests simples pour améliorer la couverture."""
    
    def test_genealogy_stats_success(self, client_with_mock_service, mock_service):
        """Test récupération des statistiques - succès"""
        mock_service.get_stats.return_value = {
            "total_persons": 5,
            "total_families": 2,
            "total_events": 10,
            "metadata": {
                "source_file": "test.gw",
                "created": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z",
                "version": "1.0.0",
                "encoding": "utf-8"
            },
            "persons_by_sex": {"male": 3, "female": 2, "unknown": 0},
            "persons_by_access_level": {"public": 5, "private": 0},
            "families_by_status": {"married": 2, "divorced": 0},
            "events_by_type": {"birth": 5, "death": 3, "marriage": 2},
            "average_children_per_family": 1.5
        }
        
        response = client_with_mock_service.get("/api/v1/genealogy/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_persons"] == 5
    
    def test_genealogy_stats_error(self, client_with_mock_service, mock_service):
        """Test récupération des statistiques - erreur"""
        mock_service.get_stats.side_effect = Exception("Erreur de service")
        
        response = client_with_mock_service.get("/api/v1/genealogy/stats")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_genealogy_health(self, client_with_mock_service):
        """Test endpoint de santé"""
        response = client_with_mock_service.get("/api/v1/genealogy/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_genealogy_export_gedcom(self, client_with_mock_service, mock_service):
        """Test export GEDCOM"""
        mock_service.export_gedcom.return_value = b"GEDCOM content"
        
        response = client_with_mock_service.get("/api/v1/genealogy/export/gedcom")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
    
    def test_genealogy_export_json(self, client_with_mock_service, mock_service):
        """Test export JSON"""
        mock_service.export_json.return_value = '{"persons": []}'
        
        response = client_with_mock_service.get("/api/v1/genealogy/export/json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_genealogy_export_xml(self, client_with_mock_service, mock_service):
        """Test export XML"""
        mock_service.export_xml.return_value = '<?xml version="1.0"?><genealogy></genealogy>'
        
        response = client_with_mock_service.get("/api/v1/genealogy/export/xml")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
    
    def test_genealogy_export_unsupported(self, client_with_mock_service):
        """Test export format non supporté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/unsupported")
        
        assert response.status_code == 400
        data = response.json()
        assert "Format non supporté" in data["detail"]
    
    def test_genealogy_search_success(self, client_with_mock_service, mock_service):
        """Test recherche - succès"""
        mock_service.search_persons.return_value = []
        
        response = client_with_mock_service.get("/api/v1/genealogy/search?query=test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_genealogy_search_no_query(self, client_with_mock_service):
        """Test recherche sans query"""
        response = client_with_mock_service.get("/api/v1/genealogy/search")
        
        assert response.status_code == 400
        data = response.json()
        assert "query" in data["detail"]
    
    def test_genealogy_search_error(self, client_with_mock_service, mock_service):
        """Test recherche - erreur"""
        mock_service.search_persons.side_effect = Exception("Erreur de recherche")
        
        response = client_with_mock_service.get("/api/v1/genealogy/search?query=test")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_persons_list_success(self, client_with_mock_service, mock_service):
        """Test liste des personnes - succès"""
        mock_service.get_persons.return_value = []
        
        response = client_with_mock_service.get("/api/v1/persons")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_persons_list_error(self, client_with_mock_service, mock_service):
        """Test liste des personnes - erreur"""
        mock_service.get_persons.side_effect = Exception("Erreur de service")
        
        response = client_with_mock_service.get("/api/v1/persons")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_families_list_success(self, client_with_mock_service, mock_service):
        """Test liste des familles - succès"""
        mock_service.get_families.return_value = []
        
        response = client_with_mock_service.get("/api/v1/families")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_families_list_error(self, client_with_mock_service, mock_service):
        """Test liste des familles - erreur"""
        mock_service.get_families.side_effect = Exception("Erreur de service")
        
        response = client_with_mock_service.get("/api/v1/families")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_events_list_success(self, client_with_mock_service, mock_service):
        """Test liste des événements - succès"""
        mock_service.get_events.return_value = []
        
        response = client_with_mock_service.get("/api/v1/events")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_events_list_error(self, client_with_mock_service, mock_service):
        """Test liste des événements - erreur"""
        mock_service.get_events.side_effect = Exception("Erreur de service")
        
        response = client_with_mock_service.get("/api/v1/events")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
