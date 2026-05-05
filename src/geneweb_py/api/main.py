"""
Application FastAPI principale pour l'API geneweb-py.

Cette application fournit une API REST moderne pour manipuler les données
généalogiques au format GeneWeb (.gw).
"""

from typing import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import Response

from .limits import CORS_ALLOW_ORIGINS
from .middleware.error_handler import setup_error_handlers
from .middleware.logging import setup_logging_middleware
from .rate_limit import limiter
from .routers import events, families, genealogy, persons
from .services.genealogy_service import GenealogyService

_genealogy_service = GenealogyService()


def get_global_genealogy_service() -> GenealogyService:
    """Retourne le service global de généalogie."""
    return _genealogy_service


app = FastAPI(
    title="GeneWeb-py API",
    description="API REST moderne pour manipuler les fichiers généalogiques au format GeneWeb (.gw)",  # noqa: E501
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def add_security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Ajoute des en-têtes HTTP de sécurité de base."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    )
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy",
        (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        ),
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

setup_logging_middleware(app)
setup_error_handlers(app)

app.include_router(
    persons.router,
    prefix="/api/v1/persons",
    tags=["Personnes"],
)

app.include_router(
    families.router,
    prefix="/api/v1/families",
    tags=["Familles"],
)

app.include_router(
    events.router,
    prefix="/api/v1/events",
    tags=["Événements"],
)

app.include_router(
    genealogy.router,
    prefix="/api/v1/genealogy",
    tags=["Généalogie"],
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """
    Vérification de l'état de santé de l'API.

    Returns:
        JSONResponse: Statut de l'API
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "GeneWeb-py API is running",
            "version": "0.1.0",
        }
    )


@app.get("/")
async def root() -> JSONResponse:
    """
    Route racine de l'API.

    Returns:
        JSONResponse: Informations sur l'API
    """
    return JSONResponse(
        content={
            "message": "Bienvenue sur l'API GeneWeb-py",
            "version": "0.1.0",
            "documentation": "/docs",
            "redoc": "/redoc",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "geneweb_py.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
