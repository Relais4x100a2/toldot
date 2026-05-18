# Ephemeral Session Token (Privacy by Design) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le singleton `GenealogyService` global par un store de sessions éphémères en mémoire, avec token opaque par utilisateur, TTL glissant d'1 heure, nettoyage automatique, et mode READ_ONLY configurable.

**Architecture:** Un `SessionStore` (threading.Lock + dict en mémoire) est stocké dans `app.state`. L'upload `.gw` crée une session et retourne un token `secrets.token_urlsafe(32)`. Tous les endpoints lisent `X-Session-Token` pour résoudre la `Genealogy` de session via une nouvelle dépendance FastAPI `get_session_service()`. Une coroutine asyncio purge les sessions expirées toutes les 5 minutes.

**Tech Stack:** FastAPI, Python 3.12, pytest, httpx/TestClient, threading.Lock, secrets

**Spec:** `docs/superpowers/specs/2026-05-18-ephemeral-session-design.md`

---

## Carte des fichiers

**Créer :**
- `src/geneweb_py/api/session_store.py` — `SessionEntry`, `SessionFullError`, `SessionStore`
- `src/geneweb_py/api/routers/sessions.py` — `POST /api/v1/sessions`, `DELETE /api/v1/sessions/{token}`
- `tests/api/test_session_store.py` — tests unitaires de `SessionStore`
- `tests/api/test_sessions_router.py` — tests d'intégration du router sessions

**Modifier :**
- `src/geneweb_py/api/limits.py` — ajouter `READ_ONLY`, `SESSION_MAX_SESSIONS`, `SESSION_TTL_SECONDS`
- `src/geneweb_py/api/services/genealogy_service.py` — `__init__` accepte `genealogy: Optional[Genealogy]`
- `src/geneweb_py/api/dependencies.py` — ajouter `get_store`, `get_session_service`, `require_write_mode` ; supprimer les anciennes
- `src/geneweb_py/api/main.py` — lifespan, supprimer singleton, enregistrer sessions router
- `src/geneweb_py/api/routers/genealogy.py` — supprimer `import`/`clear`, mettre à jour dépendances
- `src/geneweb_py/api/routers/persons.py` — `get_session_service` + `require_write_mode` sur mutants
- `src/geneweb_py/api/routers/families.py` — idem
- `src/geneweb_py/api/routers/events.py` — idem
- `src/geneweb_py/api/middleware/logging.py` — exclure `X-Session-Token` des logs
- `tests/api/test_main.py` — supprimer import `get_global_genealogy_service`
- `tests/api/test_routers_genealogy.py` — adapter aux sessions
- `tests/api/test_routers_persons.py` — adapter aux sessions
- `tests/api/test_routers_families.py` — adapter aux sessions
- `tests/api/test_routers_events.py` — adapter aux sessions

---

## Task 1 : Settings — nouvelles variables d'environnement

**Files:**
- Modify: `src/geneweb_py/api/limits.py`

- [ ] **Step 1 : Ajouter les constantes à limits.py**

Ajouter à la fin du fichier `src/geneweb_py/api/limits.py` (après la ligne `MAX_UPLOAD_BYTES`) :

```python
SESSION_MAX_SESSIONS: int = _parse_int_env("SESSION_MAX_SESSIONS", 10)
SESSION_TTL_SECONDS: int = _parse_int_env("SESSION_TTL_SECONDS", 3600)
READ_ONLY: bool = os.getenv("READ_ONLY", "false").strip().lower() == "true"
```

- [ ] **Step 2 : Vérifier que les imports existants ne cassent pas**

```bash
python -c "from geneweb_py.api.limits import SESSION_MAX_SESSIONS, SESSION_TTL_SECONDS, READ_ONLY, MAX_UPLOAD_BYTES; print('OK', SESSION_MAX_SESSIONS, SESSION_TTL_SECONDS, READ_ONLY)"
```

Attendu : `OK 10 3600 False`

- [ ] **Step 3 : Commit**

```bash
git add src/geneweb_py/api/limits.py
git commit -m "feat(api): ajouter SESSION_MAX_SESSIONS, SESSION_TTL_SECONDS, READ_ONLY à limits"
```

---

## Task 2 : SessionStore — store de sessions éphémères

**Files:**
- Create: `src/geneweb_py/api/session_store.py`
- Create: `tests/api/test_session_store.py`

- [ ] **Step 1 : Écrire les tests unitaires**

Créer `tests/api/test_session_store.py` :

```python
"""Tests unitaires pour SessionStore."""
from datetime import datetime, timedelta, timezone

import pytest

from geneweb_py.api.session_store import SessionFullError, SessionStore
from geneweb_py.core.genealogy import Genealogy


def _make_genealogy() -> Genealogy:
    return Genealogy()


class TestSessionStoreCreate:
    def test_create_returns_token_and_expiry(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        g = _make_genealogy()
        token, expires_at = store.create(g)
        assert len(token) > 20
        assert isinstance(expires_at, datetime)
        assert expires_at > datetime.now(timezone.utc)

    def test_create_stores_genealogy(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        g = _make_genealogy()
        token, _ = store.create(g)
        assert store.get(token) is g

    def test_create_raises_when_full(self):
        store = SessionStore(max_sessions=2, ttl_seconds=3600)
        store.create(_make_genealogy())
        store.create(_make_genealogy())
        with pytest.raises(SessionFullError):
            store.create(_make_genealogy())

    def test_tokens_are_unique(self):
        store = SessionStore(max_sessions=10, ttl_seconds=3600)
        tokens = {store.create(_make_genealogy())[0] for _ in range(5)}
        assert len(tokens) == 5


class TestSessionStoreGet:
    def test_get_unknown_returns_none(self):
        store = SessionStore()
        assert store.get("nonexistent") is None

    def test_get_extends_ttl(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        g = _make_genealogy()
        token, _ = store.create(g)
        before = store._store[token].expires_at
        store.get(token)
        after = store._store[token].expires_at
        assert after >= before

    def test_get_expired_returns_none(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        token, _ = store.create(_make_genealogy())
        store._store[token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert store.get(token) is None

    def test_get_removes_expired_entry(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        token, _ = store.create(_make_genealogy())
        store._store[token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        store.get(token)
        assert token not in store._store


class TestSessionStoreDelete:
    def test_delete_existing(self):
        store = SessionStore()
        token, _ = store.create(_make_genealogy())
        assert store.delete(token) is True
        assert store.get(token) is None

    def test_delete_unknown(self):
        store = SessionStore()
        assert store.delete("nonexistent") is False


class TestSessionStoreCleanup:
    def test_cleanup_removes_expired(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        token, _ = store.create(_make_genealogy())
        store._store[token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        count = store.cleanup_expired()
        assert count == 1
        assert token not in store._store

    def test_cleanup_preserves_active(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        token, _ = store.create(_make_genealogy())
        count = store.cleanup_expired()
        assert count == 0
        assert store.get(token) is not None


class TestSessionStoreCountAndFull:
    def test_count_active(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        assert store.count_active() == 0
        store.create(_make_genealogy())
        assert store.count_active() == 1

    def test_is_full(self):
        store = SessionStore(max_sessions=2, ttl_seconds=3600)
        assert not store.is_full()
        store.create(_make_genealogy())
        store.create(_make_genealogy())
        assert store.is_full()

    def test_expired_not_counted(self):
        store = SessionStore(max_sessions=5, ttl_seconds=3600)
        token, _ = store.create(_make_genealogy())
        store._store[token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert store.count_active() == 0
```

- [ ] **Step 2 : Vérifier que les tests échouent (module absent)**

```bash
pytest tests/api/test_session_store.py -v 2>&1 | head -10
```

Attendu : `ImportError` ou `ModuleNotFoundError` sur `session_store`.

- [ ] **Step 3 : Créer `session_store.py`**

Créer `src/geneweb_py/api/session_store.py` :

```python
"""Store de sessions éphémères en mémoire — privacy by design."""

import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from ..core.genealogy import Genealogy
from .limits import SESSION_MAX_SESSIONS, SESSION_TTL_SECONDS


class SessionFullError(Exception):
    """Levée quand le cap de sessions simultanées est atteint."""


@dataclass
class SessionEntry:
    genealogy: Genealogy
    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SessionStore:
    """Store en mémoire de sessions éphémères avec TTL glissant."""

    def __init__(
        self,
        max_sessions: int = SESSION_MAX_SESSIONS,
        ttl_seconds: int = SESSION_TTL_SECONDS,
    ) -> None:
        self._max = max_sessions
        self._ttl = ttl_seconds
        self._store: Dict[str, SessionEntry] = {}
        self._lock = threading.Lock()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _new_expiry(self) -> datetime:
        return self._now() + timedelta(seconds=self._ttl)

    def create(self, genealogy: Genealogy) -> Tuple[str, datetime]:
        """Crée une session, lève SessionFullError si le cap est atteint."""
        with self._lock:
            active = sum(1 for e in self._store.values() if e.expires_at > self._now())
            if active >= self._max:
                raise SessionFullError("Session cap reached")
            token = secrets.token_urlsafe(32)
            expires_at = self._new_expiry()
            self._store[token] = SessionEntry(genealogy=genealogy, expires_at=expires_at)
            return token, expires_at

    def get(self, token: str) -> Optional[Genealogy]:
        """Retourne la Genealogy si la session est active, None sinon. Prolonge le TTL."""
        entry = self._store.get(token)
        if entry is None:
            return None
        if entry.expires_at <= self._now():
            with self._lock:
                self._store.pop(token, None)
            return None
        with self._lock:
            entry.expires_at = self._new_expiry()
        return entry.genealogy

    def delete(self, token: str) -> bool:
        """Supprime une session. Retourne True si trouvée, False sinon."""
        with self._lock:
            if token in self._store:
                del self._store[token]
                return True
        return False

    def cleanup_expired(self) -> int:
        """Supprime les sessions expirées. Retourne le nombre supprimé."""
        now = self._now()
        with self._lock:
            expired = [k for k, e in self._store.items() if e.expires_at <= now]
            for k in expired:
                del self._store[k]
        return len(expired)

    def count_active(self) -> int:
        """Nombre de sessions non expirées."""
        now = self._now()
        return sum(1 for e in self._store.values() if e.expires_at > now)

    def is_full(self) -> bool:
        """Vrai si le cap de sessions est atteint."""
        return self.count_active() >= self._max
```

- [ ] **Step 4 : Lancer les tests**

```bash
pytest tests/api/test_session_store.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 5 : Commit**

```bash
git add src/geneweb_py/api/session_store.py tests/api/test_session_store.py
git commit -m "feat(api): ajouter SessionStore éphémère avec TTL glissant et cap de sessions"
```

---

## Task 3 : GenealogyService — accepter une Genealogy existante

**Files:**
- Modify: `src/geneweb_py/api/services/genealogy_service.py:56-61`

- [ ] **Step 1 : Écrire le test**

Ajouter dans `tests/api/test_services.py` (après les imports existants) :

```python
def test_genealogy_service_accepts_existing_genealogy(sample_genealogy):
    from geneweb_py.api.services.genealogy_service import GenealogyService
    service = GenealogyService(genealogy=sample_genealogy)
    assert service.genealogy is sample_genealogy
    assert len(service.genealogy.persons) == len(sample_genealogy.persons)
```

- [ ] **Step 2 : Vérifier que le test échoue**

```bash
pytest tests/api/test_services.py::test_genealogy_service_accepts_existing_genealogy -v
```

Attendu : `FAILED` — `TypeError: __init__() got an unexpected keyword argument 'genealogy'`

- [ ] **Step 3 : Modifier `GenealogyService.__init__`**

Dans `src/geneweb_py/api/services/genealogy_service.py`, remplacer `__init__` (lignes 56-61) :

```python
def __init__(self, genealogy: Optional[Genealogy] = None) -> None:
    """Initialise le service de généalogie."""
    self._genealogy: Optional[Genealogy] = None
    self._parser = GeneWebParser(use_multipass=False)
    if genealogy is not None:
        self._genealogy = genealogy
    else:
        self._initialize_empty_genealogy()
```

- [ ] **Step 4 : Lancer les tests**

```bash
pytest tests/api/test_services.py -v
```

Attendu : tous les tests passent (y compris le nouveau).

- [ ] **Step 5 : Commit**

```bash
git add src/geneweb_py/api/services/genealogy_service.py tests/api/test_services.py
git commit -m "feat(api): GenealogyService accepte une Genealogy existante en paramètre"
```

---

## Task 4 : Nouvelles dépendances FastAPI

**Files:**
- Modify: `src/geneweb_py/api/dependencies.py`

- [ ] **Step 1 : Réécrire `dependencies.py`**

Remplacer l'intégralité de `src/geneweb_py/api/dependencies.py` par :

```python
"""Dépendances FastAPI pour l'API geneweb-py."""

from typing import Generator, Tuple

from fastapi import Depends, Header, HTTPException, Request, status

from .limits import READ_ONLY
from .session_store import SessionStore
from .services.genealogy_service import GenealogyService


def get_store(request: Request) -> SessionStore:
    """Retourne le SessionStore stocké dans app.state."""
    return request.app.state.session_store


def get_session_service(
    x_session_token: str = Header(..., alias="X-Session-Token"),
    store: SessionStore = Depends(get_store),
) -> GenealogyService:
    """Résout le token de session et retourne un GenealogyService wrappant la Genealogy."""
    genealogy = store.get(x_session_token)
    if genealogy is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session inconnue ou expirée",
        )
    return GenealogyService(genealogy=genealogy)


def require_write_mode() -> None:
    """Lève 405 si l'API est en mode lecture seule (READ_ONLY=true)."""
    if READ_ONLY:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="API en mode lecture seule",
        )


def get_pagination_params(
    page: int = 1, size: int = 20, max_size: int = 100
) -> Tuple[int, int]:
    """Valide et retourne les paramètres de pagination."""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le numéro de page doit être supérieur à 0",
        )
    if size < 1 or size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La taille de la page doit être entre 1 et {max_size}",
        )
    return page, size


def get_search_limit(limit: int = 50, max_limit: int = 100) -> int:
    """Valide et retourne la limite de recherche."""
    if limit < 1 or limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La limite doit être entre 1 et {max_limit}",
        )
    return limit
```

- [ ] **Step 2 : Vérifier l'import**

```bash
python -c "from geneweb_py.api.dependencies import get_store, get_session_service, require_write_mode; print('OK')"
```

Attendu : `OK`

- [ ] **Step 3 : Commit**

```bash
git add src/geneweb_py/api/dependencies.py
git commit -m "feat(api): remplacer get_genealogy_service par get_session_service et require_write_mode"
```

---

## Task 5 : Router sessions (POST + DELETE)

**Files:**
- Create: `src/geneweb_py/api/routers/sessions.py`
- Create: `tests/api/test_sessions_router.py`

- [ ] **Step 1 : Écrire les tests**

Créer `tests/api/test_sessions_router.py` :

```python
"""Tests d'intégration pour le router /api/v1/sessions."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURE_GW = Path(__file__).parent.parent / "fixtures" / "simple_test.gw"


@pytest.fixture
def client(tmp_path):
    from geneweb_py.api.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c


def _upload_gw(client, path: Path = FIXTURE_GW) -> dict:
    with open(path, "rb") as f:
        resp = client.post(
            "/api/v1/sessions",
            files={"file": ("simple_test.gw", f, "application/octet-stream")},
        )
    return resp


class TestCreateSession:
    def test_create_returns_201(self, client):
        resp = _upload_gw(client)
        assert resp.status_code == 201

    def test_create_returns_token_and_expiry(self, client):
        data = _upload_gw(client).json()
        assert "session_token" in data
        assert "expires_at" in data
        assert len(data["session_token"]) > 20

    def test_create_returns_stats(self, client):
        data = _upload_gw(client).json()
        assert "stats" in data
        assert "persons" in data["stats"]
        assert "families" in data["stats"]

    def test_create_cache_control_no_store(self, client):
        resp = _upload_gw(client)
        assert resp.headers.get("cache-control") == "no-store"

    def test_create_wrong_extension_returns_400(self, client, tmp_path):
        bad = tmp_path / "file.txt"
        bad.write_bytes(b"content")
        with open(bad, "rb") as f:
            resp = client.post(
                "/api/v1/sessions",
                files={"file": ("file.txt", f, "text/plain")},
            )
        assert resp.status_code == 400

    def test_create_invalid_mime_returns_415(self, client):
        with open(FIXTURE_GW, "rb") as f:
            resp = client.post(
                "/api/v1/sessions",
                files={"file": ("test.gw", f, "application/pdf")},
            )
        assert resp.status_code == 415


class TestDeleteSession:
    def test_delete_returns_204(self, client):
        token = _upload_gw(client).json()["session_token"]
        resp = client.delete(f"/api/v1/sessions/{token}")
        assert resp.status_code == 204

    def test_delete_unknown_returns_404(self, client):
        resp = client.delete("/api/v1/sessions/unknowntoken")
        assert resp.status_code == 404

    def test_token_invalid_after_delete(self, client):
        token = _upload_gw(client).json()["session_token"]
        client.delete(f"/api/v1/sessions/{token}")
        resp = client.get("/api/v1/persons/", headers={"X-Session-Token": token})
        assert resp.status_code == 401
```

- [ ] **Step 2 : Vérifier que les tests échouent**

```bash
pytest tests/api/test_sessions_router.py -v 2>&1 | head -15
```

Attendu : erreurs d'import (module sessions absent) ou 404 (route absente).

- [ ] **Step 3 : Créer `routers/sessions.py`**

Créer `src/geneweb_py/api/routers/sessions.py` :

```python
"""Router FastAPI pour la gestion des sessions éphémères."""

import os
import tempfile
from pathlib import Path
from typing import Optional, Set

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from ...core.parser import GeneWebParser
from ..dependencies import get_store
from ..limits import MAX_UPLOAD_BYTES
from ..rate_limit import limiter
from ..session_store import SessionFullError, SessionStore

router = APIRouter()

_ALLOWED_CONTENT_TYPES: Set[str] = {
    "application/octet-stream",
    "text/plain",
    "application/genealogy",
}
_READ_CHUNK_SIZE = 1024 * 1024


def _sanitize_filename(raw: str) -> str:
    return Path(raw).name if raw else ""


def _validate_meta(content_type: Optional[str], name: str) -> None:
    if not name.lower().endswith((".gw", ".gwplus")):
        raise HTTPException(400, "Le fichier doit avoir l'extension .gw ou .gwplus")
    if content_type is not None:
        main_type = content_type.split(";")[0].strip().lower()
        if main_type not in {t.lower() for t in _ALLOWED_CONTENT_TYPES}:
            raise HTTPException(415, "Type de contenu non accepté pour un fichier GeneWeb")


@router.post("/", status_code=201)
@limiter.limit("5/hour")
async def create_session(
    request: Request,
    file: UploadFile = File(...),
    store: SessionStore = Depends(get_store),
) -> JSONResponse:
    """
    Crée une session éphémère à partir d'un fichier .gw uploadé.

    Returns:
        JSONResponse: { session_token, expires_at, stats }
    """
    safe_name = _sanitize_filename(file.filename or "")
    _validate_meta(file.content_type, safe_name)

    if store.is_full():
        raise HTTPException(503, "Serveur saturé, réessayez plus tard")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".gw") as tmp:
        tmp_path = tmp.name
        total = 0
        while True:
            chunk = await file.read(_READ_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                tmp.flush()
                os.unlink(tmp_path)
                raise HTTPException(
                    413,
                    f"Fichier trop volumineux (limite {MAX_UPLOAD_BYTES // (1024 * 1024)} Mo)",
                )
            tmp.write(chunk)

    try:
        parser = GeneWebParser(use_multipass=False)
        genealogy = parser.parse_file(tmp_path)
        genealogy.metadata.source_file = None
    except Exception as exc:
        raise HTTPException(422, f"Erreur de parsing : {exc}") from exc
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    try:
        token, expires_at = store.create(genealogy)
    except SessionFullError:
        raise HTTPException(503, "Serveur saturé, réessayez plus tard")

    return JSONResponse(
        status_code=201,
        content={
            "session_token": token,
            "expires_at": expires_at.isoformat(),
            "stats": {
                "persons": len(genealogy.persons),
                "families": len(genealogy.families),
            },
        },
        headers={"Cache-Control": "no-store"},
    )


@router.delete("/{token}", status_code=204)
async def delete_session(
    token: str,
    store: SessionStore = Depends(get_store),
) -> None:
    """Supprime explicitement une session (privacy by design)."""
    if not store.delete(token):
        raise HTTPException(404, "Session inconnue ou expirée")
```

- [ ] **Step 4 : Enregistrer le router dans `main.py`**

Dans `src/geneweb_py/api/main.py`, ajouter l'import en haut (avec les autres imports de routers) :

```python
from .routers import events, families, genealogy, persons, sessions
```

Ajouter le lifespan et modifier `create_app` pour enregistrer le router sessions et supprimer le singleton. Remplacer le contenu de `main.py` par :

```python
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
```

- [ ] **Step 5 : Lancer les tests du router sessions**

```bash
pytest tests/api/test_sessions_router.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 6 : Commit**

```bash
git add src/geneweb_py/api/routers/sessions.py src/geneweb_py/api/main.py tests/api/test_sessions_router.py
git commit -m "feat(api): router sessions éphémères POST/DELETE + lifespan SessionStore"
```

---

## Task 6 : Router genealogy — mise à jour des dépendances

**Files:**
- Modify: `src/geneweb_py/api/routers/genealogy.py`
- Modify: `tests/api/test_routers_genealogy.py`

- [ ] **Step 1 : Mettre à jour le router genealogy**

Dans `src/geneweb_py/api/routers/genealogy.py` :

1. Remplacer l'import :
```python
# Avant
from ..dependencies import get_genealogy_service
# Après
from ..dependencies import get_session_service
```

2. Supprimer la fonction `import_genealogy_file` (endpoint `POST /import`) — elle est remplacée par `POST /api/v1/sessions`.

3. Supprimer la fonction `clear_genealogy` (endpoint `DELETE /`) — plus de sens sans singleton.

4. Dans tous les endpoints restants (`export_genealogy`, `get_genealogy_stats`, `search_genealogy`, `validate_genealogy`), remplacer :
```python
service: GenealogyService = Depends(get_genealogy_service)
```
par :
```python
service: GenealogyService = Depends(get_session_service)
```

5. Supprimer les imports devenus inutiles (`os`, `tempfile`, les validateurs d'upload si plus utilisés). Garder `_export_with_cleanup` et `_unlink_temp` pour les exports.

- [ ] **Step 2 : Lancer les tests genealogy existants**

```bash
pytest tests/api/test_routers_genealogy.py tests/api/test_routers_genealogy_complete.py -v 2>&1 | tail -20
```

Certains tests vont échouer (ceux qui utilisent l'ancien flow import/clear ou le singleton). Identifier lesquels.

- [ ] **Step 3 : Mettre à jour les tests genealogy**

Dans `tests/api/test_routers_genealogy.py` et `tests/api/test_routers_genealogy_complete.py` :

Ajouter une fixture de session partagée (en tête de chaque fichier) :

```python
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

FIXTURE_GW = Path(__file__).parent.parent / "fixtures" / "simple_test.gw"


@pytest.fixture
def client_with_token():
    from geneweb_py.api.main import create_app
    app = create_app()
    with TestClient(app) as c:
        with open(FIXTURE_GW, "rb") as f:
            resp = c.post(
                "/api/v1/sessions",
                files={"file": ("simple_test.gw", f, "application/octet-stream")},
            )
        token = resp.json()["session_token"]
        yield c, token
```

Remplacer dans chaque test `client` par `client_with_token` et passer `headers={"X-Session-Token": token}` à chaque requête. Supprimer les tests relatifs aux endpoints supprimés (`import`, `clear`).

- [ ] **Step 4 : Lancer les tests**

```bash
pytest tests/api/test_routers_genealogy.py tests/api/test_routers_genealogy_complete.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 5 : Commit**

```bash
git add src/geneweb_py/api/routers/genealogy.py tests/api/test_routers_genealogy.py tests/api/test_routers_genealogy_complete.py
git commit -m "refactor(api): router genealogy migré vers sessions éphémères"
```

---

## Task 7 : Router persons — mise à jour des dépendances

**Files:**
- Modify: `src/geneweb_py/api/routers/persons.py`
- Modify: `tests/api/test_routers_persons.py`

- [ ] **Step 1 : Mettre à jour le router persons**

Dans `src/geneweb_py/api/routers/persons.py`, effectuer deux changements :

**a) Remplacer l'import :**
```python
# Avant
from ..dependencies import get_genealogy_service
# Après
from ..dependencies import get_session_service, require_write_mode
```

**b) Remplacer `get_genealogy_service` par `get_session_service` sur tous les endpoints :**
```python
# Avant
service: GenealogyService = Depends(get_genealogy_service)
# Après
service: GenealogyService = Depends(get_session_service)
```

**c) Ajouter `require_write_mode` aux endpoints mutants :**
```python
# create_person :
@router.post("/", response_model=SuccessResponse, status_code=201, dependencies=[Depends(require_write_mode)])
async def create_person(
    person_data: PersonCreateSchema,
    service: GenealogyService = Depends(get_session_service),
) -> SuccessResponse:

# update_person :
@router.put("/{person_id}", response_model=SuccessResponse, dependencies=[Depends(require_write_mode)])
async def update_person(
    person_id: str,
    person_data: PersonUpdateSchema,
    service: GenealogyService = Depends(get_session_service),
) -> SuccessResponse:

# delete_person :
@router.delete("/{person_id}", response_model=SuccessResponse, dependencies=[Depends(require_write_mode)])
async def delete_person(
    person_id: str, service: GenealogyService = Depends(get_session_service)
) -> SuccessResponse:
```

- [ ] **Step 2 : Mettre à jour les tests persons**

Dans `tests/api/test_routers_persons.py`, ajouter la fixture `client_with_token` (même code que Task 6 Step 3) et mettre à jour chaque test pour passer le header `X-Session-Token`.

Pattern à appliquer sur chaque requête :
```python
# Avant
response = client.get("/api/v1/persons/")
# Après
response = client.get("/api/v1/persons/", headers={"X-Session-Token": token})
```

- [ ] **Step 3 : Lancer les tests**

```bash
pytest tests/api/test_routers_persons.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 4 : Commit**

```bash
git add src/geneweb_py/api/routers/persons.py tests/api/test_routers_persons.py
git commit -m "refactor(api): router persons migré vers sessions + require_write_mode"
```

---

## Task 8 : Router families — mise à jour des dépendances

**Files:**
- Modify: `src/geneweb_py/api/routers/families.py`
- Modify: `tests/api/test_routers_families.py`

- [ ] **Step 1 : Mettre à jour le router families**

Appliquer exactement les mêmes changements qu'en Task 7, sur `families.py` :

```python
# Import
from ..dependencies import get_session_service, require_write_mode

# Tous les Depends(get_genealogy_service) → Depends(get_session_service)

# Endpoints mutants reçoivent dependencies=[Depends(require_write_mode)] :
# - POST /  (create_family)
# - PUT /{family_id}  (update_family)
# - DELETE /{family_id}  (delete_family)
```

- [ ] **Step 2 : Mettre à jour les tests families**

Dans `tests/api/test_routers_families.py` : ajouter `client_with_token`, passer `X-Session-Token` sur toutes les requêtes.

- [ ] **Step 3 : Lancer les tests**

```bash
pytest tests/api/test_routers_families.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 4 : Commit**

```bash
git add src/geneweb_py/api/routers/families.py tests/api/test_routers_families.py
git commit -m "refactor(api): router families migré vers sessions + require_write_mode"
```

---

## Task 9 : Router events — mise à jour des dépendances

**Files:**
- Modify: `src/geneweb_py/api/routers/events.py`
- Modify: `tests/api/test_routers_events.py`

- [ ] **Step 1 : Mettre à jour le router events**

Dans `src/geneweb_py/api/routers/events.py` :

```python
# Import
from ..dependencies import get_session_service, require_write_mode

# Tous les Depends(get_genealogy_service) → Depends(get_session_service)

# Endpoints mutants reçoivent dependencies=[Depends(require_write_mode)] :
# - POST /personal  (create_personal_event)
# - POST /family    (create_family_event)
# - PUT /{event_id} (update_event)
# - DELETE /{event_id} (delete_event)
```

- [ ] **Step 2 : Mettre à jour les tests events**

Dans `tests/api/test_routers_events.py` : même pattern — `client_with_token` + header `X-Session-Token`.

- [ ] **Step 3 : Lancer les tests**

```bash
pytest tests/api/test_routers_events.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 4 : Commit**

```bash
git add src/geneweb_py/api/routers/events.py tests/api/test_routers_events.py
git commit -m "refactor(api): router events migré vers sessions + require_write_mode"
```

---

## Task 10 : Mise à jour de test_main.py

**Files:**
- Modify: `tests/api/test_main.py`

- [ ] **Step 1 : Mettre à jour test_main.py**

Dans `tests/api/test_main.py`, supprimer l'import :
```python
# Supprimer cette ligne
from geneweb_py.api.main import app, get_global_genealogy_service
```

Remplacer par :
```python
from geneweb_py.api.main import app
```

Supprimer le test `test_get_global_service` (la fonction n'existe plus).

Les autres tests (`test_app_creation`, `test_root_endpoint`, `test_security_headers_on_root`, `test_health_endpoint`) fonctionnent sans changement.

- [ ] **Step 2 : Lancer les tests**

```bash
pytest tests/api/test_main.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 3 : Lancer la suite complète**

```bash
pytest tests/ -v --ignore=tests/performance -q
```

Attendu : tous les tests passent. Vérifier la couverture reste ≥ 80 % :

```bash
pytest --cov=geneweb_py --cov-report=term-missing -q
```

- [ ] **Step 4 : Commit**

```bash
git add tests/api/test_main.py
git commit -m "refactor(tests): adapter test_main au nouveau lifespan sans singleton global"
```

---

## Task 11 : Middleware logging — exclure X-Session-Token

**Files:**
- Modify: `src/geneweb_py/api/middleware/logging.py`

- [ ] **Step 1 : Écrire le test**

Dans `tests/api/test_middleware.py`, ajouter :

```python
def test_session_token_not_logged(caplog):
    import logging
    from pathlib import Path
    from fastapi.testclient import TestClient
    from geneweb_py.api.main import create_app

    FIXTURE_GW = Path(__file__).parent.parent / "fixtures" / "simple_test.gw"
    app = create_app()
    secret_token = "SUPERSECRET_SESSION_TOKEN_12345"

    with TestClient(app) as client, caplog.at_level(logging.INFO):
        with open(FIXTURE_GW, "rb") as f:
            client.post(
                "/api/v1/sessions",
                files={"file": ("simple_test.gw", f, "application/octet-stream")},
            )
        client.get("/api/v1/persons/", headers={"X-Session-Token": secret_token})

    for record in caplog.records:
        assert secret_token not in record.getMessage()
```

- [ ] **Step 2 : Vérifier que le test échoue**

```bash
pytest tests/api/test_middleware.py::test_session_token_not_logged -v
```

Attendu : `FAILED` si le token apparaît dans les logs, `PASSED` si déjà absent (le middleware actuel ne logue pas les headers — vérifier).

Si le test passe déjà, passer directement au Step 4. Sinon :

- [ ] **Step 3 : Modifier `LoggingMiddleware.dispatch`**

Dans `src/geneweb_py/api/middleware/logging.py`, dans la méthode `dispatch`, s'assurer que le log ne contient jamais la valeur du header `X-Session-Token`. Le log actuel n'inclut que method, path, IP et user-agent — le header n'est donc pas loggé. Ajouter explicitement un commentaire documentant cette garantie :

```python
# X-Session-Token n'est intentionnellement pas inclus dans les logs (privacy by design)
logger.info(
    "Requête entrante: %s %s depuis %s - User-Agent: %s",
    request.method,
    request.url.path,
    client_ip,
    user_agent_sanitized,
)
```

- [ ] **Step 4 : Lancer le test**

```bash
pytest tests/api/test_middleware.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 5 : Commit**

```bash
git add src/geneweb_py/api/middleware/logging.py tests/api/test_middleware.py
git commit -m "feat(api): garantir que X-Session-Token n'est pas loggé (privacy by design)"
```

---

## Task 12 : Test d'intégration — flux complet de session

**Files:**
- Create: `tests/api/test_session_integration.py`

- [ ] **Step 1 : Écrire le test d'intégration complet**

Créer `tests/api/test_session_integration.py` :

```python
"""Test d'intégration du flux complet de session éphémère."""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURE_GW = Path(__file__).parent.parent / "fixtures" / "simple_test.gw"


@pytest.fixture
def client():
    from geneweb_py.api.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c


def _create_session(client) -> str:
    with open(FIXTURE_GW, "rb") as f:
        resp = client.post(
            "/api/v1/sessions",
            files={"file": ("simple_test.gw", f, "application/octet-stream")},
        )
    assert resp.status_code == 201
    return resp.json()["session_token"]


class TestFullSessionFlow:
    def test_upload_query_delete(self, client):
        token = _create_session(client)

        # Consulter les personnes
        resp = client.get("/api/v1/persons/", headers={"X-Session-Token": token})
        assert resp.status_code == 200

        # Supprimer la session
        resp = client.delete(f"/api/v1/sessions/{token}")
        assert resp.status_code == 204

        # Token révoqué
        resp = client.get("/api/v1/persons/", headers={"X-Session-Token": token})
        assert resp.status_code == 401

    def test_missing_token_returns_422(self, client):
        resp = client.get("/api/v1/persons/")
        assert resp.status_code == 422

    def test_expired_token_returns_401(self, client):
        from datetime import datetime, timedelta, timezone
        token = _create_session(client)
        store = client.app.state.session_store
        store._store[token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        resp = client.get("/api/v1/persons/", headers={"X-Session-Token": token})
        assert resp.status_code == 401

    def test_session_cap_returns_503(self, client):
        store = client.app.state.session_store
        original_max = store._max
        store._max = 1
        try:
            _create_session(client)
            with open(FIXTURE_GW, "rb") as f:
                resp = client.post(
                    "/api/v1/sessions",
                    files={"file": ("simple_test.gw", f, "application/octet-stream")},
                )
            assert resp.status_code == 503
        finally:
            store._max = original_max

    def test_two_sessions_are_isolated(self, client):
        token1 = _create_session(client)
        token2 = _create_session(client)

        resp1 = client.get("/api/v1/persons/", headers={"X-Session-Token": token1})
        resp2 = client.get("/api/v1/persons/", headers={"X-Session-Token": token2})
        assert resp1.status_code == 200
        assert resp2.status_code == 200

        client.delete(f"/api/v1/sessions/{token1}")
        resp1_after = client.get("/api/v1/persons/", headers={"X-Session-Token": token1})
        resp2_after = client.get("/api/v1/persons/", headers={"X-Session-Token": token2})
        assert resp1_after.status_code == 401
        assert resp2_after.status_code == 200

    def test_source_file_not_stored(self, client):
        token = _create_session(client)
        store = client.app.state.session_store
        genealogy = store._store[token].genealogy
        assert genealogy.metadata.source_file is None


class TestReadOnlyMode:
    def test_write_blocked_in_read_only_mode(self, client, monkeypatch):
        import geneweb_py.api.limits as limits_module
        monkeypatch.setattr(limits_module, "READ_ONLY", True)

        # Recréer la dépendance avec la nouvelle valeur
        import geneweb_py.api.dependencies as dep_module
        monkeypatch.setattr(dep_module, "READ_ONLY", True)

        token = _create_session(client)
        resp = client.post(
            "/api/v1/persons/",
            json={"first_name": "Jean", "surname": "Dupont", "sex": "M"},
            headers={"X-Session-Token": token},
        )
        assert resp.status_code == 405

    def test_reads_allowed_in_read_only_mode(self, client, monkeypatch):
        import geneweb_py.api.dependencies as dep_module
        monkeypatch.setattr(dep_module, "READ_ONLY", True)

        token = _create_session(client)
        resp = client.get("/api/v1/persons/", headers={"X-Session-Token": token})
        assert resp.status_code == 200
```

- [ ] **Step 2 : Lancer les tests d'intégration**

```bash
pytest tests/api/test_session_integration.py -v
```

Attendu : tous les tests passent.

- [ ] **Step 3 : Lancer la suite complète avec couverture**

```bash
pytest tests/ --ignore=tests/performance -q --cov=geneweb_py --cov-report=term-missing
```

Attendu : tous les tests passent, couverture ≥ 80 %.

- [ ] **Step 4 : Commit final**

```bash
git add tests/api/test_session_integration.py
git commit -m "test(api): tests d'intégration du flux complet de session éphémère"
```

---

## Vérification finale

```bash
# Lint
ruff check src/ tests/

# Typage
mypy src/geneweb_py/

# Suite complète
pytest tests/ --ignore=tests/performance -q

# Couverture
pytest --cov=geneweb_py --cov-report=html
```

Vérifier dans le rapport HTML que `session_store.py`, `routers/sessions.py` et `dependencies.py` sont couverts.
