"""Application FastAPI principale pour l'API geneweb-py."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import Response

from .limits import get_cors_allow_origins
from .middleware.error_handler import setup_error_handlers
from .middleware.logging import setup_logging_middleware
from .rate_limit import limiter
from .routers import events, families, genealogy, persons, sessions
from .session_store import SessionStore


async def _cleanup_loop(store: SessionStore) -> None:
    while True:
        await asyncio.sleep(300)
        store.cleanup_expired()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    store = SessionStore()
    application.state.session_store = store
    task = asyncio.create_task(_cleanup_loop(store))
    yield
    task.cancel()


def create_app() -> FastAPI:
    """Construit l'application FastAPI (middlewares, routeurs)."""
    application = FastAPI(
        title="GeneWeb-py API",
        description=(
            "API REST moderne pour manipuler les fichiers généalogiques "
            "au format GeneWeb (.gw)"
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)

    @application.middleware("http")
    async def add_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        _docs_paths = {"/docs", "/redoc", "/openapi.json"}
        if request.url.path in _docs_paths:
            csp = (
                "default-src 'self'; "
                "script-src 'unsafe-inline' cdn.jsdelivr.net; "
                "style-src 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src data: fastapi.tiangolo.com; "
                "connect-src 'self' cdn.jsdelivr.net"
            )
        else:
            csp = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            (
                "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
                "magnetometer=(), microphone=(), payment=(), usb=()"
            ),
        )
        return response

    application.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Session-Token"],
    )

    setup_logging_middleware(application)
    setup_error_handlers(application)

    application.include_router(
        sessions.router,
        prefix="/api/v1/sessions",
        tags=["Sessions"],
    )
    application.include_router(
        persons.router,
        prefix="/api/v1/persons",
        tags=["Personnes"],
    )
    application.include_router(
        families.router,
        prefix="/api/v1/families",
        tags=["Familles"],
    )
    application.include_router(
        events.router,
        prefix="/api/v1/events",
        tags=["Événements"],
    )
    application.include_router(
        genealogy.router,
        prefix="/api/v1/genealogy",
        tags=["Généalogie"],
    )

    @application.get("/health")
    async def health_check() -> JSONResponse:
        return JSONResponse(
            content={
                "status": "healthy",
                "message": "GeneWeb-py API is running",
                "version": "0.1.0",
            }
        )

    @application.get("/")
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "message": "Bienvenue sur l'API GeneWeb-py",
                "version": "0.1.0",
                "documentation": "/docs",
                "redoc": "/redoc",
            }
        )

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "geneweb_py.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
