"""
Tests d'intégration pour l'API FastAPI geneweb-py.

Ces tests vérifient le fonctionnement complet de l'API avec des données réelles.
"""

import pytest
from fastapi.testclient import TestClient
from geneweb_py.api.main import app
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.models import Gender, AccessLevel, MarriageStatus, EventType
from tests.api.test_service import TestGenealogyService


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def test_service():
    """Service de test avec isolation des données."""
    return TestGenealogyService()


@pytest.fixture
def client_with_test_service(test_service):
    """Client de test avec service isolé."""
    from geneweb_py.api.dependencies import get_genealogy_service
    from geneweb_py.api.main import app
    
    # Override de la dépendance
    def get_test_service():
        return test_service
    
    app.dependency_overrides[get_genealogy_service] = get_test_service
    
    client = TestClient(app)
    
    yield client
    
    # Restaurer les dépendances originales
    app.dependency_overrides.clear()


class TestAPIIntegration:
    """Tests d'intégration complets de l'API."""
    
    def test_health_check(self, client):
        """Test de l'endpoint de santé."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "GeneWeb-py API is running" in data["message"]
    
    def test_root_endpoint(self, client):
        """Test de l'endpoint racine."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Bienvenue sur l'API GeneWeb-py" in data["message"]
        assert "/docs" in data["documentation"]
    
    def test_person_crud_workflow(self, client):
        """Test complet du workflow CRUD pour les personnes."""
        # 1. Créer une personne
        person_data = {
            "first_name": "Jean",
            "surname": "Dupont",
            "public_name": "Jean Dupont",
            "sex": "male",
            "access_level": "public",
            "titles": []
        }
        
        response = client.post("/api/v1/persons", json=person_data)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Personne créée avec succès"
        person_id = data["data"]["id"]
        
        # 2. Récupérer la personne
        response = client.get(f"/api/v1/persons/{person_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["first_name"] == "Jean"
        assert data["data"]["surname"] == "Dupont"
        
        # 3. Mettre à jour la personne
        update_data = {
            "first_name": "Jean-Pierre",
            "public_name": "Jean-Pierre Dupont"
        }
        response = client.put(f"/api/v1/persons/{person_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["first_name"] == "Jean-Pierre"
        
        # 4. Lister les personnes
        response = client.get("/api/v1/persons")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1
        
        # 5. Supprimer la personne
        response = client.delete(f"/api/v1/persons/{person_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Personne supprimée avec succès"
        
        # 6. Vérifier que la personne est supprimée
        response = client.get(f"/api/v1/persons/{person_id}")
        assert response.status_code == 404
    
    def test_family_crud_workflow(self, client):
        """Test complet du workflow CRUD pour les familles."""
        # 1. Créer deux personnes pour la famille
        husband_data = {
            "first_name": "Pierre",
            "surname": "Martin",
            "sex": "male",
            "access_level": "public",
            "titles": []
        }
        wife_data = {
            "first_name": "Marie",
            "surname": "Durand",
            "sex": "female",
            "access_level": "public",
            "titles": []
        }
        
        # Créer le mari
        response = client.post("/api/v1/persons", json=husband_data)
        assert response.status_code == 201
        husband_id = response.json()["data"]["id"]
        
        # Créer la femme
        response = client.post("/api/v1/persons", json=wife_data)
        assert response.status_code == 201
        wife_id = response.json()["data"]["id"]
        
        # 2. Créer une famille
        family_data = {
            "husband_id": husband_id,
            "wife_id": wife_id,
            "marriage_status": "married",
            "children": [],
            "notes": ["Famille de test"],
            "sources": []
        }
        
        response = client.post("/api/v1/families", json=family_data)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Famille créée avec succès"
        family_id = data["data"]["id"]
        
        # 3. Récupérer la famille
        response = client.get(f"/api/v1/families/{family_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["husband_id"] == husband_id
        assert data["data"]["wife_id"] == wife_id
        
        # 4. Lister les familles
        response = client.get("/api/v1/families")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1
        
        # 5. Supprimer la famille
        response = client.delete(f"/api/v1/families/{family_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Famille supprimée avec succès"
    
    def test_event_creation_workflow(self, client_with_test_service):
        """Test de création d'événements."""
        # 1. Créer une personne
        person_data = {
            "first_name": "Paul",
            "surname": "Bernard",
            "sex": "male",
            "access_level": "public",
            "titles": []
        }
        
        response = client_with_test_service.post("/api/v1/persons", json=person_data)
        assert response.status_code == 201
        person_id = response.json()["data"]["id"]
        
        # 2. Créer un événement personnel
        event_data = {
            "person_id": person_id,
            "event_type": "birth",
            "place": "Paris, France",
            "note": "Événement de test",
            "witnesses": [],
            "sources": []
        }
        
        response = client_with_test_service.post("/api/v1/events/personal", json=event_data)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Événement personnel créé avec succès"
        assert data["data"]["person_id"] == person_id
        
        # 3. Lister les événements
        response = client_with_test_service.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
    
    def test_genealogy_stats(self, client_with_test_service):
        """Test des statistiques de généalogie."""
        # Créer quelques données de test
        persons_data = [
            {"first_name": "Alice", "surname": "Martin", "sex": "female", "access_level": "public", "titles": []},
            {"first_name": "Bob", "surname": "Martin", "sex": "male", "access_level": "public", "titles": []},
        ]
        
        for person_data in persons_data:
            response = client_with_test_service.post("/api/v1/persons", json=person_data)
            assert response.status_code == 201
        
        # Récupérer les statistiques
        response = client_with_test_service.get("/api/v1/genealogy/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_persons"] == 2
        assert data["data"]["total_families"] == 0
    
    def test_search_functionality(self, client_with_test_service):
        """Test de la fonctionnalité de recherche."""
        # Créer des données de test
        persons_data = [
            {"first_name": "Alice", "surname": "Martin", "sex": "female", "access_level": "public", "titles": []},
            {"first_name": "Bob", "surname": "Durand", "sex": "male", "access_level": "public", "titles": []},
        ]
        
        for person_data in persons_data:
            response = client_with_test_service.post("/api/v1/persons", json=person_data)
            assert response.status_code == 201
        
        # Rechercher par nom
        response = client_with_test_service.get("/api/v1/genealogy/search?query=Martin")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_results"] >= 1
        assert len(data["data"]["results"]["persons"]) >= 1
        
        # Rechercher par prénom
        response = client_with_test_service.get("/api/v1/genealogy/search?query=Alice")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_results"] >= 1
    
    def test_error_handling(self, client):
        """Test de la gestion d'erreurs."""
        # Test 404 pour personne inexistante
        response = client.get("/api/v1/persons/nonexistent")
        assert response.status_code == 404
        
        # Test validation des données
        invalid_person_data = {
            "first_name": "",  # Nom vide
            "surname": "Test",
            "sex": "invalid_sex",  # Sexe invalide
            "access_level": "public",
            "titles": []
        }
        
        response = client.post("/api/v1/persons", json=invalid_person_data)
        assert response.status_code == 422  # Validation error
    
    def test_pagination(self, client_with_test_service):
        """Test de la pagination."""
        # Créer plusieurs personnes
        for i in range(25):
            person_data = {
                "first_name": f"Person{i}",
                "surname": "Test",
                "sex": "male",
                "access_level": "public",
                "titles": []
            }
            response = client_with_test_service.post("/api/v1/persons", json=person_data)
            assert response.status_code == 201
        
        # Test pagination première page
        response = client_with_test_service.get("/api/v1/persons?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["has_next"] is True
        
        # Test pagination deuxième page
        response = client_with_test_service.get("/api/v1/persons?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["pagination"]["page"] == 2
        
        # Test pagination dernière page
        response = client_with_test_service.get("/api/v1/persons?page=3&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["pagination"]["page"] == 3
        assert data["pagination"]["has_next"] is False


class TestAPIPerformance:
    """Tests de performance de l'API."""
    
    def test_bulk_operations(self, client_with_test_service):
        """Test des opérations en lot."""
        import time
        
        # Créer 50 personnes rapidement
        start_time = time.time()
        
        for i in range(50):
            person_data = {
                "first_name": f"Person{i}",
                "surname": "Bulk",
                "sex": "male",
                "access_level": "public",
                "titles": []
            }
            response = client_with_test_service.post("/api/v1/persons", json=person_data)
            assert response.status_code == 201
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Vérifier que l'opération est raisonnablement rapide (< 10 secondes)
        assert duration < 10.0
        
        # Vérifier que toutes les personnes ont été créées
        response = client_with_test_service.get("/api/v1/persons")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total"] == 50
    
    def test_concurrent_requests(self, client_with_test_service):
        """Test de requêtes concurrentes."""
        import threading
        import time
        
        results = []
        
        def create_person(person_id, test_client):
            person_data = {
                "first_name": f"Concurrent{person_id}",
                "surname": "Test",
                "sex": "male",
                "access_level": "public",
                "titles": []
            }
            response = test_client.post("/api/v1/persons", json=person_data)
            results.append(response.status_code)
        
        # Créer 10 threads simultanés
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_person, args=(i, client_with_test_service))
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        # Vérifier que toutes les requêtes ont réussi
        assert all(status == 201 for status in results)
        assert len(results) == 10
