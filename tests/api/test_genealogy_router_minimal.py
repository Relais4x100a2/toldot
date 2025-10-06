"""
Tests minimaux pour le router genealogy.py - cas de base uniquement
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


class TestGenealogyRouterMinimal:
    """Tests minimaux pour le router genealogy."""
    
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
    
    def test_get_stats_success(self, client_with_mock_service, mock_service):
        """Test récupération des statistiques - succès"""
        response = client_with_mock_service.get("/api/v1/genealogy/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_persons" in data["data"]
        assert data["data"]["total_persons"] == 1
    
    def test_export_unsupported_format(self, client_with_mock_service):
        """Test export format non supporté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/unsupported")
        
        assert response.status_code == 400
        # Vérifier que la réponse contient un message d'erreur
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_export_gedcom_not_implemented(self, client_with_mock_service):
        """Test export GEDCOM non implémenté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/gedcom")
        
        assert response.status_code == 501
        # Vérifier que la réponse contient un message d'erreur
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_export_json_not_implemented(self, client_with_mock_service):
        """Test export JSON non implémenté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/json")
        
        assert response.status_code == 501
        # Vérifier que la réponse contient un message d'erreur
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_export_xml_not_implemented(self, client_with_mock_service):
        """Test export XML non implémenté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/xml")
        
        assert response.status_code == 501
        # Vérifier que la réponse contient un message d'erreur
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_export_gw_not_implemented(self, client_with_mock_service):
        """Test export GW non implémenté"""
        response = client_with_mock_service.get("/api/v1/genealogy/export/gw")
        
        assert response.status_code == 501
        # Vérifier que la réponse contient un message d'erreur
        data = response.json()
        assert "detail" in data or "message" in data
