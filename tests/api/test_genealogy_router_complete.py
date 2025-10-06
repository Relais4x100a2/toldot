"""
Tests complets pour le router genealogy.py
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
    service.export_gedcom.return_value = b"GEDCOM content"
    service.export_json.return_value = '{"persons": []}'
    service.export_xml.return_value = '<?xml version="1.0"?><genealogy></genealogy>'
    
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


class TestGenealogyRouterComplete:
    """Tests complets pour le router genealogy."""
    
    def test_import_genealogy_file_success(self, client_with_mock_service, mock_service):
        """Test import réussi d'un fichier .gw"""
        # Créer un fichier de test temporaire
        test_content = """fam DUPONT Jean + MARTIN Marie
end fam"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gw', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            # Mock du service
            mock_service.load_from_file.return_value = mock_service.genealogy
            
            # Test de l'import
            with open(temp_file_path, 'rb') as f:
                response = client_with_mock_service.post(
                    "/api/v1/genealogy/import",
                    files={"file": ("test.gw", f, "text/plain")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "test.gw" in data["message"]
            assert "statistics" in data["data"]
            
        finally:
            os.unlink(temp_file_path)
    
    def test_import_genealogy_file_wrong_extension(self, client_with_mock_service):
        """Test import avec mauvaise extension"""
        test_content = "test content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = client_with_mock_service.post(
                    "/api/v1/genealogy/import",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "extension" in data["detail"]
            
        finally:
            os.unlink(temp_file_path)
    
    def test_import_genealogy_file_error(self, client_with_mock_service, mock_service):
        """Test import avec erreur du service"""
        # Mock du service pour lever une exception
        mock_service.load_from_file.side_effect = Exception("Erreur de parsing")
        
        test_content = """fam DUPONT Jean + MARTIN Marie
end fam"""
        
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
            assert "Erreur" in data["detail"]
            
        finally:
            os.unlink(temp_file_path)
    
    def test_get_stats_success(self, client_with_mock_service, mock_service):
        """Test récupération des statistiques - succès"""
        response = client_with_mock_service.get("/api/v1/genealogy/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_persons" in data["data"]
        assert data["data"]["total_persons"] == 1
    
    def test_get_stats_error(self, client_with_mock_service, mock_service):
        """Test récupération des statistiques - erreur"""
        mock_service.get_stats.side_effect = Exception("Erreur de service")
        
        response = client_with_mock_service.get("/api/v1/genealogy/stats")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_export_gedcom_success(self, client_with_mock_service, mock_service):
        """Test export GEDCOM - succès"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/gedcom")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "content-disposition" in response.headers
    
    def test_export_gedcom_error(self, client_with_mock_service, mock_service):
        """Test export GEDCOM - erreur"""
        mock_service.export_gedcom.side_effect = Exception("Erreur d'export")
        
        response = client_with_mock_service.get("/api/v1/genealogy/export/gedcom")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_export_json_success(self, client_with_mock_service, mock_service):
        """Test export JSON - succès"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_export_json_error(self, client_with_mock_service, mock_service):
        """Test export JSON - erreur"""
        mock_service.export_json.side_effect = Exception("Erreur d'export")
        
        response = client_with_mock_service.get("/api/v1/genealogy/export/json")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_export_xml_success(self, client_with_mock_service, mock_service):
        """Test export XML - succès"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/xml")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
    
    def test_export_xml_error(self, client_with_mock_service, mock_service):
        """Test export XML - erreur"""
        mock_service.export_xml.side_effect = Exception("Erreur d'export")
        
        response = client_with_mock_service.get("/api/v1/genealogy/export/xml")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_export_unsupported_format(self, client_with_mock_service):
        """Test export format non supporté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/unsupported")
        
        assert response.status_code == 400
        data = response.json()
        assert "Format non supporté" in data["detail"]
    
    def test_search_persons_success(self, client_with_mock_service, mock_service):
        """Test recherche de personnes - succès"""
        response = client_with_mock_service.get("/api/v1/genealogy/search?query=DUPONT")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data["data"]
        assert len(data["data"]["results"]) == 1
    
    def test_search_persons_no_query(self, client_with_mock_service):
        """Test recherche sans query"""
        response = client_with_mock_service.get("/api/v1/genealogy/search")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "Field required" in str(data["detail"])
    
    def test_search_persons_error(self, client_with_mock_service, mock_service):
        """Test recherche - erreur"""
        mock_service.search_persons.side_effect = Exception("Erreur de recherche")
        
        response = client_with_mock_service.get("/api/v1/genealogy/search?query=test")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
    
    def test_get_health(self, client_with_mock_service):
        """Test endpoint de santé"""
        response = client_with_mock_service.get("/api/v1/genealogy/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_export_gw_success(self, client_with_mock_service, mock_service):
        """Test export GW - succès"""
        mock_service.export_gw.return_value = "fam DUPONT Jean\nend fam"
        
        response = client_with_mock_service.get("/api/v1/genealogy/export/gw")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain"
    
    def test_export_gw_error(self, client_with_mock_service, mock_service):
        """Test export GW - erreur"""
        mock_service.export_gw.side_effect = Exception("Erreur d'export")
        
        response = client_with_mock_service.get("/api/v1/genealogy/export/gw")
        
        assert response.status_code == 500
        data = response.json()
        assert "Erreur" in data["detail"]
