"""
Middleware de logging pour l'API geneweb-py.

Ce module fournit un logging détaillé des requêtes et réponses pour
le monitoring et le debugging.
"""

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware de logging des requêtes HTTP."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Traite la requête avec logging.

        Args:
            request: Requête HTTP
            call_next: Fonction suivante dans la chaîne

        Returns:
            Response: Réponse HTTP
        """
        # Informations de la requête
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log de la requête entrante
        logger.info(
            f"Requête entrante: {request.method} {request.url.path} "
            f"depuis {client_ip} - User-Agent: {user_agent}"
        )

        # Traitement de la requête
        try:
            response = await call_next(request)

            # Calcul du temps de traitement
            process_time = time.time() - start_time

            # Log de la réponse
            logger.info(
                f"Réponse: {request.method} {request.url.path} "
                f"-> {response.status_code} en {process_time:.3f}s"
            )

            # Ajout du temps de traitement dans les headers
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as exc:
            # Calcul du temps avant l'erreur
            process_time = time.time() - start_time

            # Log de l'erreur
            logger.error(
                f"Erreur lors du traitement: {request.method} {request.url.path} "
                f"après {process_time:.3f}s - {type(exc).__name__}: {exc}"
            )

            # Re-lance l'exception pour qu'elle soit traitée par les gestionnaires d'erreurs
            raise


def setup_logging_middleware(app: FastAPI) -> None:
    """
    Configure le middleware de logging pour l'application FastAPI.

    Args:
        app: Application FastAPI
    """
    # Ajout du middleware de logging
    app.add_middleware(LoggingMiddleware)

    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configuration spécifique pour uvicorn
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logger.info("Middleware de logging configuré pour l'API GeneWeb-py")
