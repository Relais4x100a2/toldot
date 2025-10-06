"""
Middleware de gestion d'erreurs pour l'API geneweb-py.

Ce module fournit une gestion centralisée des erreurs avec des réponses
standardisées et un logging approprié.
"""

import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ...core.exceptions import GeneWebParseError, GeneWebValidationError
from ..models.responses import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """
    Configure les gestionnaires d'erreurs pour l'application FastAPI.
    
    Args:
        app: Application FastAPI
    """
    
    @app.exception_handler(GeneWebParseError)
    async def geneweb_parse_error_handler(request: Request, exc: GeneWebParseError) -> JSONResponse:
        """Gestionnaire pour les erreurs de parsing GeneWeb."""
        logger.error(f"Erreur de parsing GeneWeb: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=True,
                message="Erreur de parsing du fichier GeneWeb",
                details=[ErrorDetail(
                    message=str(exc),
                    code="PARSE_ERROR"
                )],
                code="PARSE_ERROR"
            ).model_dump()
        )
    
    @app.exception_handler(GeneWebValidationError)
    async def geneweb_validation_error_handler(request: Request, exc: GeneWebValidationError) -> JSONResponse:
        """Gestionnaire pour les erreurs de validation GeneWeb."""
        logger.error(f"Erreur de validation GeneWeb: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=True,
                message="Erreur de validation des données GeneWeb",
                details=[ErrorDetail(
                    message=str(exc),
                    code="VALIDATION_ERROR"
                )],
                code="VALIDATION_ERROR"
            ).model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Gestionnaire pour les erreurs de validation des requêtes."""
        logger.error(f"Erreur de validation de requête: {exc}", exc_info=True)
        
        details = []
        for error in exc.errors():
            details.append(ErrorDetail(
                field=".".join(str(x) for x in error["loc"]),
                message=error["msg"],
                code=error["type"]
            ))
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=True,
                message="Erreur de validation des données de la requête",
                details=details,
                code="REQUEST_VALIDATION_ERROR"
            ).model_dump()
        )
    
    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Gestionnaire pour les erreurs HTTP."""
        logger.error(f"Erreur HTTP {exc.status_code}: {exc.detail}", exc_info=True)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=True,
                message=exc.detail,
                code=f"HTTP_{exc.status_code}"
            ).model_dump()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Gestionnaire pour les erreurs HTTP Starlette."""
        logger.error(f"Erreur Starlette HTTP {exc.status_code}: {exc.detail}", exc_info=True)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=True,
                message=exc.detail,
                code=f"STARLETTE_HTTP_{exc.status_code}"
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Gestionnaire pour toutes les autres erreurs."""
        logger.error(f"Erreur inattendue: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=True,
                message="Une erreur interne du serveur s'est produite",
                details=[ErrorDetail(
                    message="Contactez l'administrateur si le problème persiste",
                    code="INTERNAL_SERVER_ERROR"
                )],
                code="INTERNAL_SERVER_ERROR"
            ).model_dump()
        )
