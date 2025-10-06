"""
Tests très simples pour améliorer la couverture de code
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from geneweb_py.api.main import app


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


class TestCoverageSimple:
    """Tests très simples pour la couverture."""
    
    def test_genealogy_stats_success(self, client):
        """Test récupération des statistiques - succès"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
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
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/genealogy/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_persons"] == 5
    
    def test_genealogy_stats_error(self, client):
        """Test récupération des statistiques - erreur"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_stats.side_effect = Exception("Erreur de service")
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/genealogy/stats")
            
            assert response.status_code == 500
            data = response.json()
            assert "Erreur" in data["detail"]
    
    def test_genealogy_export_gedcom(self, client):
        """Test export GEDCOM"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.export_gedcom.return_value = b"GEDCOM content"
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/genealogy/export/gedcom")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
    
    def test_genealogy_export_json(self, client):
        """Test export JSON"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.export_json.return_value = '{"persons": []}'
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/genealogy/export/json")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
    
    def test_genealogy_export_xml(self, client):
        """Test export XML"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.export_xml.return_value = '<?xml version="1.0"?><genealogy></genealogy>'
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/genealogy/export/xml")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/xml"
    
    def test_genealogy_export_unsupported(self, client):
        """Test export format non supporté"""
        response = client.get("/api/v1/genealogy/export/unsupported")
        
        assert response.status_code == 400
        data = response.json()
        assert "Format non supporté" in data["detail"]
    
    def test_genealogy_search_success(self, client):
        """Test recherche - succès"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.search_persons.return_value = []
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/genealogy/search?query=test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_genealogy_search_no_query(self, client):
        """Test recherche sans query"""
        response = client.get("/api/v1/genealogy/search")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "Field required" in str(data["detail"])
    
    def test_genealogy_search_error(self, client):
        """Test recherche - erreur"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.search_persons.side_effect = Exception("Erreur de recherche")
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/genealogy/search?query=test")
            
            assert response.status_code == 500
            data = response.json()
            assert "Erreur" in data["detail"]
    
    def test_persons_list_success(self, client):
        """Test liste des personnes - succès"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_persons.return_value = []
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/persons")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_persons_list_error(self, client):
        """Test liste des personnes - erreur"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_persons.side_effect = Exception("Erreur de service")
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/persons")
            
            assert response.status_code == 500
            data = response.json()
            assert "Erreur" in data["detail"]
    
    def test_families_list_success(self, client):
        """Test liste des familles - succès"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_families.return_value = []
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/families")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_families_list_error(self, client):
        """Test liste des familles - erreur"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_families.side_effect = Exception("Erreur de service")
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/families")
            
            assert response.status_code == 500
            data = response.json()
            assert "Erreur" in data["detail"]
    
    def test_events_list_success(self, client):
        """Test liste des événements - succès"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_events.return_value = []
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/events")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_events_list_error(self, client):
        """Test liste des événements - erreur"""
        with patch('geneweb_py.api.dependencies.get_genealogy_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_events.side_effect = Exception("Erreur de service")
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/events")
            
            assert response.status_code == 500
            data = response.json()
            assert "Erreur" in data["detail"]
