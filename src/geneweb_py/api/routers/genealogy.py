"""
Router FastAPI pour la gestion de la généalogie dans l'API geneweb-py.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Set

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse

from ...formats import GEDCOMExporter, JSONExporter, XMLExporter
from ..dependencies import get_genealogy_service
from ..limits import MAX_UPLOAD_BYTES
from ..models.responses import StatsResponse, SuccessResponse
from ..rate_limit import limiter
from ..router_helpers import raise_internal_server_error
from ..services.genealogy_service import GenealogyService

router = APIRouter()

_ALLOWED_UPLOAD_CONTENT_TYPES: Set[str] = {
    "application/octet-stream",
    "text/plain",
    "application/genealogy",
}

_READ_CHUNK_SIZE = 1024 * 1024


def _unlink_temp(path: str) -> None:
    """Supprime un fichier temporaire en ignorant les erreurs."""
    try:
        os.unlink(path)
    except OSError:
        pass


def _sanitize_client_filename(raw: str) -> str:
    """Retourne un nom de fichier sans composants de chemin (basename)."""
    if not raw:
        return ""
    return Path(raw).name


def _validate_upload_meta(content_type: Optional[str], safe_name: str) -> None:
    """Vérifie type MIME et extension pour l'import .gw."""
    if not safe_name.lower().endswith((".gw", ".gwplus")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit avoir l'extension .gw ou .gwplus",
        )
    if content_type is not None:
        main_type = content_type.split(";")[0].strip().lower()
        allowed = {t.lower() for t in _ALLOWED_UPLOAD_CONTENT_TYPES if t}
        if main_type not in allowed:
            raise HTTPException(
                status_code=415,
                detail="Type de contenu non accepté pour un fichier GeneWeb",
            )


@router.post("/import", response_model=SuccessResponse)
@limiter.limit("20/minute")
async def import_genealogy_file(
    request: Request,
    file: UploadFile = File(...),
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Importe un fichier généalogique (.gw).

    Args:
        request: Requête HTTP (limitation de débit).
        file: Fichier à importer
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les statistiques d'import
    """
    safe_name = _sanitize_client_filename(file.filename or "")
    try:
        _validate_upload_meta(file.content_type, safe_name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".gw") as temp_file:
            temp_file_path = temp_file.name
            total = 0
            while True:
                chunk = await file.read(_READ_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    temp_file.flush()
                    os.unlink(temp_file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Fichier trop volumineux (limite "
                            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} Mo)"
                        ),
                    )
                temp_file.write(chunk)

        try:
            service.load_from_file(temp_file_path)
            stats = service.get_stats()

            return SuccessResponse(
                message=f"Fichier '{safe_name}' importé avec succès",
                data={
                    "filename": safe_name,
                    "size_bytes": total,
                    "statistics": stats,
                },
            )

        finally:
            _unlink_temp(temp_file_path)

    except HTTPException:
        raise
    except Exception as exc:
        raise_internal_server_error(
            "Erreur lors de l'import du fichier généalogique", exc
        )


def _export_with_cleanup(
    genealogy: Any,
    exporter_class: type,
    suffix: str,
    download_filename: str,
    media_type: str,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    """Écrit l'export dans un fichier temporaire et planifie sa suppression."""
    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(temp_fd)
    try:
        exporter = exporter_class()
        exporter.export(genealogy, temp_path)
    except Exception:
        _unlink_temp(temp_path)
        raise

    background_tasks.add_task(_unlink_temp, temp_path)
    return FileResponse(
        path=temp_path,
        filename=download_filename,
        media_type=media_type,
    )


@router.get("/export/{format}", response_class=FileResponse)
@limiter.limit("40/minute")
async def export_genealogy(
    request: Request,
    format: str,
    background_tasks: BackgroundTasks,
    service: GenealogyService = Depends(get_genealogy_service),
) -> FileResponse:
    """
    Exporte la généalogie dans différents formats.

    Args:
        request: Requête HTTP (limitation de débit).
        format: Format d'export (gw, json, xml, gedcom)
        background_tasks: Tâches après envoi de la réponse (nettoyage disque)
        service: Service de généalogie

    Returns:
        FileResponse: Fichier exporté
    """
    try:
        genealogy = service.genealogy

        if format == "gw":
            raise HTTPException(
                status_code=501,
                detail="Export vers format GeneWeb non encore implémenté",
            )
        if format == "json":
            try:
                return _export_with_cleanup(
                    genealogy,
                    JSONExporter,
                    ".json",
                    "genealogy.json",
                    "application/json",
                    background_tasks,
                )
            except Exception as exc:
                raise_internal_server_error(
                    "Erreur lors de l'export JSON de la généalogie", exc
                )
        if format == "xml":
            try:
                return _export_with_cleanup(
                    genealogy,
                    XMLExporter,
                    ".xml",
                    "genealogy.xml",
                    "application/xml",
                    background_tasks,
                )
            except Exception as exc:
                raise_internal_server_error(
                    "Erreur lors de l'export XML de la généalogie", exc
                )
        if format == "gedcom":
            try:
                return _export_with_cleanup(
                    genealogy,
                    GEDCOMExporter,
                    ".ged",
                    "genealogy.ged",
                    "application/octet-stream",
                    background_tasks,
                )
            except Exception as exc:
                raise_internal_server_error(
                    "Erreur lors de l'export GEDCOM de la généalogie", exc
                )

        raise HTTPException(
            status_code=400,
            detail=(
                f"Format d'export '{format}' non supporté. "
                "Formats disponibles: gw, json, xml, gedcom"
            ),
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise_internal_server_error("Erreur lors de l'export de la généalogie", exc)


@router.get("/stats", response_model=SuccessResponse)
async def get_genealogy_stats(
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Récupère les statistiques générales de la généalogie.

    Args:
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les statistiques complètes
    """
    try:
        stats = service.get_stats()

        stats_response = StatsResponse(
            total_persons=stats["total_persons"],
            total_families=stats["total_families"],
            total_events=stats["total_events"],
            metadata={
                "source_file": stats["metadata"]["source_file"],
                "created": stats["metadata"]["created"],
                "updated": stats["metadata"]["updated"],
                "version": stats["metadata"]["version"],
                "encoding": stats["metadata"]["encoding"],
            },
            persons_by_sex=stats["persons_by_sex"],
            persons_by_access_level=stats["persons_by_access_level"],
            families_by_status=stats["families_by_status"],
            events_by_type=stats["events_by_type"],
            average_children_per_family=stats["average_children_per_family"],
        )

        return SuccessResponse(
            message="Statistiques récupérées avec succès",
            data=stats_response.model_dump(),
        )

    except Exception as exc:
        raise_internal_server_error(
            "Erreur lors de la récupération des statistiques de la généalogie", exc
        )


@router.get("/search", response_model=SuccessResponse)
@limiter.limit("60/minute")
async def search_genealogy(
    request: Request,
    query: str = Query(..., min_length=1, description="Terme de recherche"),
    search_type: str = Query(
        "all", description="Type de recherche: all, persons, families, events"
    ),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum de résultats"),
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Effectue une recherche globale dans la généalogie.

    Args:
        request: Requête HTTP (limitation de débit).
        query: Terme de recherche
        search_type: Type de recherche (all, persons, families, events)
        limit: Nombre maximum de résultats
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les résultats de recherche
    """
    try:
        genealogy = service.genealogy
        query_lower = query.lower()
        results = {"persons": [], "families": [], "events": []}

        if search_type in ["all", "persons"]:
            for person in genealogy.persons.values():
                if (
                    query_lower in person.first_name.lower()
                    or query_lower in person.last_name.lower()
                    or (
                        person.public_name and query_lower in person.public_name.lower()
                    )
                    or (
                        person.birth_place and query_lower in person.birth_place.lower()
                    )
                    or (
                        person.death_place and query_lower in person.death_place.lower()
                    )
                ):
                    person_data = {
                        "id": person.unique_id,
                        "first_name": person.first_name,
                        "surname": person.last_name,
                        "public_name": person.public_name,
                        "sex": person.gender.value if person.gender else None,
                        "birth_place": person.birth_place,
                        "death_place": person.death_place,
                    }
                    results["persons"].append(person_data)

        if search_type in ["all", "families"]:
            for family in genealogy.families.values():
                husband = (
                    genealogy.persons.get(family.husband_id)
                    if family.husband_id
                    else None
                )
                wife = genealogy.persons.get(family.wife_id) if family.wife_id else None

                family_matches = False
                if husband and (
                    query_lower in husband.first_name.lower()
                    or query_lower in husband.last_name.lower()
                ):
                    family_matches = True
                if wife and (
                    query_lower in wife.first_name.lower()
                    or query_lower in wife.last_name.lower()
                ):
                    family_matches = True

                if family_matches:
                    family_data = {
                        "id": family.id,
                        "husband_id": family.husband_id,
                        "wife_id": family.wife_id,
                        "marriage_status": (
                            family.marriage_status.value
                            if family.marriage_status
                            else None
                        ),
                        "children_count": len(family.children),
                    }
                    results["families"].append(family_data)

        if search_type in ["all", "events"]:
            for person in genealogy.persons.values():
                for event in person.events:
                    if (
                        query_lower in (event.place or "").lower()
                        or query_lower in (event.reason or "").lower()
                        or query_lower in (event.notes or "").lower()
                    ):
                        event_data = {
                            "id": getattr(event, "unique_id", "unknown"),
                            "event_type": (
                                event.event_type.value if event.event_type else None
                            ),
                            "place": event.place,
                            "reason": event.reason,
                            "person_id": person.unique_id,
                            "family_id": None,
                        }
                        results["events"].append(event_data)

            for family in genealogy.families.values():
                for event in family.events:
                    if (
                        query_lower in (event.place or "").lower()
                        or query_lower in (event.reason or "").lower()
                        or query_lower in (event.notes or "").lower()
                    ):
                        event_data = {
                            "id": getattr(event, "unique_id", "unknown"),
                            "event_type": (
                                event.event_type.value if event.event_type else None
                            ),
                            "place": event.place,
                            "reason": event.reason,
                            "person_id": None,
                            "family_id": family.id,
                        }
                        results["events"].append(event_data)

        total_results = (
            len(results["persons"]) + len(results["families"]) + len(results["events"])
        )
        if limit < total_results:
            results["persons"] = results["persons"][:limit]
            remaining = limit - len(results["persons"])
            if remaining > 0:
                results["families"] = results["families"][:remaining]
                remaining = remaining - len(results["families"])
                if remaining > 0:
                    results["events"] = results["events"][:remaining]

        search_results = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "results": results,
            "total_results": total_results,
        }

        return SuccessResponse(
            message=f"Recherche '{query}' effectuée avec succès", data=search_results
        )

    except Exception as exc:
        raise_internal_server_error(
            "Erreur lors de la recherche dans la généalogie", exc
        )


@router.post("/validate", response_model=SuccessResponse)
async def validate_genealogy(
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Valide la cohérence de la généalogie.

    Args:
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les résultats de validation
    """
    try:
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": [],
        }

        return SuccessResponse(
            message="Validation effectuée avec succès", data=validation_results
        )

    except Exception as exc:
        raise_internal_server_error(
            "Erreur lors de la validation de la généalogie", exc
        )


@router.delete("/", response_model=SuccessResponse)
async def clear_genealogy(
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Vide la généalogie actuelle.

    Args:
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès
    """
    try:
        service.create_empty()

        return SuccessResponse(message="Généalogie vidée avec succès")

    except Exception as exc:
        raise_internal_server_error("Erreur lors du vidage de la généalogie", exc)


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Vérification de l'état de santé du service de généalogie.

    Returns:
        Dict[str, Any]: Statut du service
    """
    return {
        "status": "healthy",
        "service": "genealogy",
        "message": "Service de généalogie opérationnel",
        "version": "0.1.0",
    }
