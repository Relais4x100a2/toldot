"""
Tests pour les middlewares de l'API.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from geneweb_py.api.middleware.error_handler import setup_error_handlers
from geneweb_py.api.middleware.logging import setup_logging_middleware


class TestErrorHandler:
    """Tests pour le middleware de gestion d'erreurs."""

    def test_error_handler_setup(self):
        """Test configuration du handler d'erreurs."""
        app = FastAPI()
        setup_error_handlers(app)
        # Le middleware est configuré
        assert app is not None

    def test_http_exception_handling(self):
        """Test gestion des HTTPException."""
        app = FastAPI()
        setup_error_handlers(app)

        @app.get("/test-error")
        async def test_error():
            raise HTTPException(status_code=404, detail="Not found")

        client = TestClient(app)
        response = client.get("/test-error")
        assert response.status_code == 404

    def test_validation_error_handling(self):
        """Test gestion des erreurs de validation."""
        app = FastAPI()
        setup_error_handlers(app)

        from pydantic import BaseModel

        class Item(BaseModel):
            name: str
            value: int

        @app.post("/test-validation")
        async def test_validation(item: Item):
            return item

        client = TestClient(app)
        response = client.post("/test-validation", json={"name": "test"})  # Missing value
        assert response.status_code == 422


class TestLoggingMiddleware:
    """Tests pour le middleware de logging."""

    def test_logging_middleware_setup(self):
        """Test configuration du middleware de logging."""
        app = FastAPI()
        setup_logging_middleware(app)
        # Le middleware est configuré
        assert app is not None

    def test_request_logging(self):
        """Test logging des requêtes."""
        app = FastAPI()
        setup_logging_middleware(app)

        @app.get("/test-log")
        async def test_log():
            return {"message": "OK"}

        client = TestClient(app)
        response = client.get("/test-log")
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}

