"""Application FastAPI principale pour l'API geneweb-py."""

import asyncio
import pathlib
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable, Tuple

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import Response
from starlette.routing import Match, Mount
from starlette.types import Scope

from .limits import get_cors_allow_origins
from .middleware.error_handler import setup_error_handlers
from .middleware.logging import setup_logging_middleware
from .rate_limit import limiter
from .routers import events, families, genealogy, persons, sessions
from .session_store import SessionStore


class _StaticMount(Mount):
    """A Starlette Mount that only matches GET/HEAD requests.

    Mounting StaticFiles at "/" makes ``Mount.matches()`` return FULL for every
    path and every HTTP method, which bypasses FastAPI's redirect_slashes logic
    for mutation endpoints (e.g. POST /api/v1/sessions → 405 instead of the
    expected 307 redirect to POST /api/v1/sessions/).

    This subclass returns NONE for non-GET/HEAD requests so that Starlette's
    Router can fall through to its redirect_slashes path and properly redirect
    mutation requests that are missing a trailing slash.
    """

    def matches(self, scope: Scope) -> Tuple[Any, Any]:
        if scope.get("type") == "http" and scope.get("method", "GET") not in (
            "GET",
            "HEAD",
        ):
            return Match.NONE, {}
        return super().matches(scope)


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
        elif request.url.path.startswith("/api/v1/"):
            csp = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        else:
            # Front-end statique — 'unsafe-inline' requis pour les style="" dans le HTML et JS
            csp = (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'"
            )
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            (
                "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
                "magnetometer=(), microphone=(), payment=(), usb=()"
            ),
        )
        if request.url.path.startswith("/api/v1/"):
            response.headers.setdefault("Cache-Control", "no-store")
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

    _static_dir = pathlib.Path(__file__).parent / "static"
    if _static_dir.exists():
        _static_app = StaticFiles(directory=str(_static_dir), html=True)
        application.router.routes.append(
            _StaticMount("/", app=_static_app, name="static")
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
