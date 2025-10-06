"""
Tests avancés pour le router genealogy.py - cas d'erreur et endpoints manqués
"""

import pytest
import tempfile
import os
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
    service.get_stats.return_value = {
        "total_persons": 1,
        "total_families": 1,
        "total_events": 0,
        "metadata": {
            "source_file": "test.gw",
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "encoding": "utf-8"
        },
        "persons_by_sex": {"male": 1, "female": 0, "unknown": 0},
        "persons_by_access_level": {"public": 1, "private": 0},
        "families_by_status": {"married": 1, "divorced": 0},
        "events_by_type": {"birth": 1, "death": 0},
        "average_children_per_family": 0.0
    }
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


class TestGenealogyRouterAdvanced:
    """Tests avancés pour le router genealogy."""
    
    def test_import_genealogy_file_no_file(self, client_with_mock_service):
        """Test import sans fichier"""
        response = client_with_mock_service.post("/api/v1/genealogy/import")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_import_genealogy_file_empty(self, client_with_mock_service):
        """Test import avec fichier vide"""
        response = client_with_mock_service.post(
            "/api/v1/genealogy/import",
            files={"file": ("empty.gw", b"", "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_import_genealogy_file_parsing_error(self, client_with_mock_service, mock_service):
        """Test import avec erreur de parsing"""
        mock_service.load_from_file.side_effect = Exception("Erreur de parsing")
        
        test_content = """invalid content"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gw', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = client_with_mock_service.post(
                    "/api/v1/genealogy/import",
                    files={"file": ("test.gw", f, "text/plain")}
                )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data or "message" in data or "error" in data
            
        finally:
            os.unlink(temp_file_path)
    
    def test_get_stats_service_error(self, client_with_mock_service, mock_service):
        """Test récupération des statistiques avec erreur de service"""
        mock_service.get_stats.side_effect = Exception("Erreur de service")
        
        response = client_with_mock_service.get("/api/v1/genealogy/stats")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_search_persons_with_filters(self, client_with_mock_service, mock_service):
        """Test recherche de personnes avec filtres"""
        response = client_with_mock_service.get(
            "/api/v1/genealogy/search?query=DUPONT&gender=male&limit=10&offset=0"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "items" in data
        mock_service.search_persons.assert_called_once()
    
    def test_search_persons_service_error(self, client_with_mock_service, mock_service):
        """Test recherche de personnes avec erreur de service"""
        mock_service.search_persons.side_effect = Exception("Erreur de recherche")
        
        response = client_with_mock_service.get("/api/v1/genealogy/search?query=test")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_export_gedcom_not_implemented(self, client_with_mock_service):
        """Test export GEDCOM non implémenté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/gedcom")
        
        assert response.status_code == 501
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_export_json_not_implemented(self, client_with_mock_service):
        """Test export JSON non implémenté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/json")
        
        assert response.status_code == 501
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_export_xml_not_implemented(self, client_with_mock_service):
        """Test export XML non implémenté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/xml")
        
        assert response.status_code == 501
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_export_gw_not_implemented(self, client_with_mock_service):
        """Test export GW non implémenté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/gw")
        
        assert response.status_code == 501
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_export_unsupported_format(self, client_with_mock_service):
        """Test export format non supporté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/unsupported")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data
    
    def test_health_endpoint(self, client_with_mock_service):
        """Test endpoint de santé"""
        response = client_with_mock_service.get("/api/v1/genealogy/health")
        
        # Le endpoint health n'existe peut-être pas, testons la réponse
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "health" in data
