"""
Tests HTTP : configuration CORS en mode production.
"""

from fastapi.testclient import TestClient

from geneweb_py.api.main import create_app


class TestCorsProduction:
    """Rejet des origines non listées lorsque l'API est en prod."""

    def test_prod_rejette_origine_non_autorisee(self, monkeypatch):
        """Une origine absente de ALLOWED_ORIGINS ne reçoit pas ACAO."""
        monkeypatch.setenv("GENEWEB_API_ENV", "prod")
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://trusted.example")
        monkeypatch.delenv("CORS_ORIGINS", raising=False)

        client = TestClient(create_app())
        response = client.get(
            "/health",
            headers={"Origin": "https://evil.example"},
        )
        assert response.headers.get("access-control-allow-origin") is None

    def test_prod_autorise_origine_listee(self, monkeypatch):
        """L'origine configurée reçoit l'en-tête CORS attendu."""
        monkeypatch.setenv("GENEWEB_API_ENV", "prod")
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://trusted.example")
        monkeypatch.delenv("CORS_ORIGINS", raising=False)

        client = TestClient(create_app())
        response = client.get(
            "/health",
            headers={"Origin": "https://trusted.example"},
        )
        assert (
            response.headers.get("access-control-allow-origin")
            == "https://trusted.example"
        )
