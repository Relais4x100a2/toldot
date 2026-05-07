"""
Tests unitaires pour la résolution des origines CORS (limits).
"""

from geneweb_py.api.limits import DEFAULT_DEV_CORS_ORIGINS, get_cors_allow_origins


class TestGetCorsAllowOrigins:
    """Comportement de ``get_cors_allow_origins`` selon l'environnement."""

    def test_prod_default_sans_variables_est_vide(self, monkeypatch):
        """En prod sans config, aucune origine par défaut (pas de wildcard)."""
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        monkeypatch.setenv("GENEWEB_API_ENV", "prod")
        assert get_cors_allow_origins() == []
        assert "*" not in get_cors_allow_origins()

    def test_dev_utilise_localhost_par_defaut(self, monkeypatch):
        """Hors prod, défaut orienté développement local."""
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        monkeypatch.setenv("GENEWEB_API_ENV", "dev")
        assert get_cors_allow_origins() == DEFAULT_DEV_CORS_ORIGINS

    def test_allowed_origins_a_priorite_sur_cors_origins(self, monkeypatch):
        """ALLOWED_ORIGINS prime sur CORS_ORIGINS (rétrocompat)."""
        monkeypatch.setenv("GENEWEB_API_ENV", "dev")
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.example")
        monkeypatch.setenv("CORS_ORIGINS", "https://b.example")
        assert get_cors_allow_origins() == ["https://a.example"]

    def test_prod_filtre_le_wildcard(self, monkeypatch):
        """En prod, * est retiré (credentials + sécurité)."""
        monkeypatch.setenv("GENEWEB_API_ENV", "prod")
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.com,*")
        assert get_cors_allow_origins() == ["https://a.com"]

    def test_cors_origins_si_allowed_absent(self, monkeypatch):
        """CORS_ORIGINS reste pris en compte si ALLOWED_ORIGINS absent."""
        monkeypatch.setenv("GENEWEB_API_ENV", "dev")
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        monkeypatch.setenv("CORS_ORIGINS", "https://legacy.example")
        assert get_cors_allow_origins() == ["https://legacy.example"]

    def test_allowed_origins_vide_explicite(self, monkeypatch):
        """Chaîne vide = aucune origine CORS."""
        monkeypatch.setenv("GENEWEB_API_ENV", "dev")
        monkeypatch.setenv("ALLOWED_ORIGINS", "")
        assert get_cors_allow_origins() == []
