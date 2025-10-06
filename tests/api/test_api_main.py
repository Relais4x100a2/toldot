"""
Tests pour l'API principale GeneWeb-py.

Ces tests vérifient le fonctionnement de base de l'API FastAPI
et des endpoints principaux.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from geneweb_py.api.main import app


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_genealogy_service():
    """Service de généalogie mocké."""
    service = Mock()
    service.genealogy = Mock()
    service.genealogy.persons = []
    service.genealogy.families = []
    service.genealogy.events = []
    service.genealogy.metadata = Mock()
    service.genealogy.metadata.name = "Test Genealogy"
    return service


class TestAPIHealth:
    """Tests pour les endpoints de santé de l'API."""
    
    def test_health_check(self, client):
        """Test de l'endpoint de vérification de santé."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "GeneWeb-py API is running"
        assert data["version"] == "0.1.0"
    
    def test_root_endpoint(self, client):
        """Test de l'endpoint racine."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Bienvenue sur l'API GeneWeb-py"
        assert data["version"] == "0.1.0"
        assert data["documentation"] == "/docs"
        assert data["redoc"] == "/redoc"


class TestAPIDocumentation:
    """Tests pour la documentation de l'API."""
    
    def test_openapi_schema(self, client):
        """Test du schéma OpenAPI."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "GeneWeb-py API"
        assert data["info"]["version"] == "0.1.0"
        assert "GeneWeb" in data["info"]["description"]
    
    def test_swagger_ui(self, client):
        """Test de l'interface Swagger UI."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "swagger" in response.text.lower()
    
    def test_redoc(self, client):
        """Test de l'interface ReDoc."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "redoc" in response.text.lower()


class TestAPIRouters:
    """Tests pour les routers de l'API."""
    
    def test_persons_router_mounted(self, client):
        """Test que le router des personnes est monté."""
        # Test d'un endpoint qui devrait fonctionner avec une généalogie vide
        response = client.get("/api/v1/persons/")
        
        # Devrait retourner 200 (liste vide)
        assert response.status_code == 200
    
    def test_families_router_mounted(self, client):
        """Test que le router des familles est monté."""
        response = client.get("/api/v1/families/")
        
        # Devrait retourner 200 (liste vide)
        assert response.status_code == 200
    
    def test_events_router_mounted(self, client):
        """Test que le router des événements est monté."""
        response = client.get("/api/v1/events/")
        
        # Devrait retourner 501 (non implémenté) ou 200
        assert response.status_code in [200, 501]
    
    def test_genealogy_router_mounted(self, client):
        """Test que le router de généalogie est monté."""
        response = client.get("/api/v1/genealogy/stats")
        
        # Devrait retourner 200 (statistiques d'une généalogie vide)
        assert response.status_code == 200


class TestAPIErrorHandling:
    """Tests pour la gestion d'erreurs de l'API."""
    
    def test_404_not_found(self, client):
        """Test des erreurs 404."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test des erreurs de méthode non autorisée."""
        response = client.post("/health")
        
        assert response.status_code == 405
    
    def test_validation_error(self, client):
        """Test des erreurs de validation."""
        # Tentative de création d'une personne avec des données invalides
        invalid_data = {
            "first_name": "",  # Prénom vide (invalide)
            "surname": "",     # Nom vide (invalide)
            "sex": "invalid"   # Sexe invalide
        }
        
        response = client.post("/api/v1/persons/", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data or "detail" in data


class TestAPICORS:
    """Tests pour la configuration CORS."""
    
    def test_cors_headers(self, client):
        """Test des headers CORS."""
        response = client.options("/health")
        
        # L'endpoint /health ne supporte pas OPTIONS
        assert response.status_code == 405
    
    def test_cors_preflight(self, client):
        """Test des requêtes preflight CORS."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = client.options("/api/v1/persons/", headers=headers)
        
        # Devrait retourner une réponse CORS valide
        assert response.status_code == 200


class TestAPIPerformance:
    """Tests de performance de base pour l'API."""
    
    def test_health_endpoint_performance(self, client):
        """Test de performance de l'endpoint de santé."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # L'endpoint de santé devrait être très rapide (< 100ms)
        assert (end_time - start_time) < 0.1
    
    def test_multiple_requests(self, client):
        """Test de plusieurs requêtes simultanées."""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.get("/health")
        
        # Faire 10 requêtes simultanées
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # Toutes les requêtes devraient réussir
        for response in responses:
            assert response.status_code == 200
