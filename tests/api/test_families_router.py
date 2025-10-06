"""
Tests spécifiques pour le router families.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from geneweb_py.api.main import app
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.family import Family, MarriageStatus


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
    husband = Person(
        last_name="DUPONT",
        first_name="Jean",
        gender=Gender.MALE
    )
    wife = Person(
        last_name="MARTIN",
        first_name="Marie",
        gender=Gender.FEMALE
    )
    genealogy.add_person(husband)
    genealogy.add_person(wife)
    
    # Créer une famille
    family = Family(
        family_id="test_family_1",
        husband_id=husband.unique_id,
        wife_id=wife.unique_id,
        marriage_status=MarriageStatus.MARRIED
    )
    genealogy.add_family(family)
    
    service.genealogy = genealogy
    service.get_family.return_value = family
    service.get_families.return_value = [family]
    service.create_family.return_value = family
    service.update_family.return_value = family
    service.delete_family.return_value = True
    
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


class TestFamiliesRouter:
    """Tests pour le router families."""
    
    def test_get_families(self, client_with_mock_service, mock_service):
        """Test récupération de toutes les familles"""
        response = client_with_mock_service.get("/api/v1/families")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "families" in data["data"]
        assert len(data["data"]["families"]) == 1
    
    def test_get_families_with_pagination(self, client_with_mock_service, mock_service):
        """Test récupération avec pagination"""
        response = client_with_mock_service.get("/api/v1/families?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "families" in data["data"]
    
    def test_get_families_with_filters(self, client_with_mock_service, mock_service):
        """Test récupération avec filtres"""
        response = client_with_mock_service.get("/api/v1/families?marriage_status=married")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_family_by_id(self, client_with_mock_service, mock_service):
        """Test récupération d'une famille par ID"""
        family_id = "test_family_id"
        mock_service.get_family.return_value = list(mock_service.genealogy.families.values())[0]
        
        response = client_with_mock_service.get(f"/api/v1/families/{family_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "family" in data["data"]
    
    def test_get_family_not_found(self, client_with_mock_service, mock_service):
        """Test récupération d'une famille inexistante"""
        mock_service.get_family.return_value = None
        
        response = client_with_mock_service.get("/api/v1/families/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "non trouvée" in data["detail"]
    
    def test_create_family(self, client_with_mock_service, mock_service):
        """Test création d'une famille"""
        family_data = {
            "husband_id": "test_husband_id",
            "wife_id": "test_wife_id",
            "marriage_status": "married"
        }
        
        response = client_with_mock_service.post("/api/v1/families", json=family_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "family" in data["data"]
    
    def test_create_family_invalid_data(self, client_with_mock_service):
        """Test création avec données invalides"""
        family_data = {
            "husband_id": "test_husband_id",
            "marriage_status": "invalid_status"
        }
        
        response = client_with_mock_service.post("/api/v1/families", json=family_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_update_family(self, client_with_mock_service, mock_service):
        """Test mise à jour d'une famille"""
        family_id = "test_family_id"
        family_data = {
            "marriage_status": "divorced",
            "notes": "Mise à jour"
        }
        
        response = client_with_mock_service.put(f"/api/v1/families/{family_id}", json=family_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "family" in data["data"]
    
    def test_update_family_not_found(self, client_with_mock_service, mock_service):
        """Test mise à jour d'une famille inexistante"""
        mock_service.update_family.return_value = None
        
        family_data = {"marriage_status": "divorced"}
        response = client_with_mock_service.put("/api/v1/families/nonexistent", json=family_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "non trouvée" in data["detail"]
    
    def test_delete_family(self, client_with_mock_service, mock_service):
        """Test suppression d'une famille"""
        family_id = "test_family_id"
        
        response = client_with_mock_service.delete(f"/api/v1/families/{family_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "supprimée" in data["message"]
    
    def test_delete_family_not_found(self, client_with_mock_service, mock_service):
        """Test suppression d'une famille inexistante"""
        mock_service.delete_family.return_value = False
        
        response = client_with_mock_service.delete("/api/v1/families/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "non trouvée" in data["detail"]
    
    def test_get_family_children(self, client_with_mock_service, mock_service):
        """Test récupération des enfants d'une famille"""
        family_id = "test_family_id"
        
        response = client_with_mock_service.get(f"/api/v1/families/{family_id}/children")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "children" in data["data"]
    
    def test_add_child_to_family(self, client_with_mock_service, mock_service):
        """Test ajout d'un enfant à une famille"""
        family_id = "test_family_id"
        child_data = {
            "person_id": "test_child_id"
        }
        
        response = client_with_mock_service.post(f"/api/v1/families/{family_id}/children", json=child_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "enfant ajouté" in data["message"]
    
    def test_remove_child_from_family(self, client_with_mock_service, mock_service):
        """Test suppression d'un enfant d'une famille"""
        family_id = "test_family_id"
        child_id = "test_child_id"
        
        response = client_with_mock_service.delete(f"/api/v1/families/{family_id}/children/{child_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "enfant supprimé" in data["message"]
