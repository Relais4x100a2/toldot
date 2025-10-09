"""
Tests pour l'application principale FastAPI.
"""

from fastapi.testclient import TestClient

from geneweb_py.api.main import app, get_global_genealogy_service


class TestMainApp:
    """Tests pour l'application FastAPI principale."""

    def test_app_creation(self):
        """Test que l'application est créée correctement."""
        assert app is not None
        assert app.title == "GeneWeb-py API"
        assert app.version == "0.1.0"

    def test_get_global_service(self):
        """Test récupération du service global."""
        service = get_global_genealogy_service()
        assert service is not None

    def test_root_endpoint(self):
        """Test endpoint racine."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Bienvenue sur l'API GeneWeb-py"
        assert data["version"] == "0.1.0"
        assert data["documentation"] == "/docs"

    def test_health_endpoint(self):
        """Test endpoint de santé."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "GeneWeb-py API is running"
        assert data["version"] == "0.1.0"

    def test_openapi_endpoint(self):
        """Test que l'OpenAPI est disponible."""
        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data

    def test_docs_endpoint(self):
        """Test que la documentation Swagger est disponible."""
        client = TestClient(app)
        response = client.get("/docs")

        assert response.status_code == 200

    def test_redoc_endpoint(self):
        """Test que ReDoc est disponible."""
        client = TestClient(app)
        response = client.get("/redoc")

        assert response.status_code == 200
