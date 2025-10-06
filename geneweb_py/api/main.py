"""
Application FastAPI principale pour l'API geneweb-py.

Cette application fournit une API REST moderne pour manipuler les données
généalogiques au format GeneWeb (.gw).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .middleware.error_handler import setup_error_handlers
from .middleware.logging import setup_logging_middleware
from .routers import persons, families, events, genealogy
from .dependencies import get_genealogy_service

# Configuration de l'application FastAPI
app = FastAPI(
    title="GeneWeb-py API",
    description="API REST moderne pour manipuler les fichiers généalogiques au format GeneWeb (.gw)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration du middleware personnalisé
setup_logging_middleware(app)
setup_error_handlers(app)

# Inclusion des routers
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

# Route de santé
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

# Route racine
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
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
