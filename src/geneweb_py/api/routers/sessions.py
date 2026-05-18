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
            raise HTTPException(
                415, "Type de contenu non accepté pour un fichier GeneWeb"
            )


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
                    f"Fichier trop volumineux "
                    f"(limite {MAX_UPLOAD_BYTES // (1024 * 1024)} Mo)",
                )
            tmp.write(chunk)

    try:
        parser = GeneWebParser(use_multipass=False)
        genealogy = parser.parse_file(tmp_path)
        genealogy.metadata.source_file = None
    except Exception as exc:
        raise HTTPException(422, "Fichier GeneWeb invalide ou corrompu") from exc
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    try:
        token, expires_at = store.create(genealogy)
    except SessionFullError as exc:
        raise HTTPException(503, "Serveur saturé, réessayez plus tard") from exc

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
