"""
Router FastAPI pour la gestion des événements dans l'API geneweb-py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_genealogy_service
from ..models.event import (
    EventSchema,
    EventUpdateSchema,
    FamilyEventCreateSchema,
    PersonalEventCreateSchema,
)
from ..models.responses import (
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
)
from ..services.genealogy_service import GenealogyService

router = APIRouter()


@router.post("/personal", response_model=SuccessResponse, status_code=201)
async def create_personal_event(
    event_data: PersonalEventCreateSchema,
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Crée un nouvel événement personnel.

    Args:
        event_data: Données de l'événement à créer
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données de l'événement
    """
    try:
        event = service.create_personal_event(event_data)

        # Conversion vers le schéma de réponse
        event_schema = EventSchema(
            id=getattr(event, "unique_id", "unknown"),
            event_type=event.event_type,
            date=None,  # TODO: Convertir les dates
            place=event.place,
            reason=event.reason,
            notes=event.notes,
            witnesses=event.witnesses,
            sources=[],  # Pas d'attribut sources dans Event
            person_id=event_data.person_id,
            family_id=None,
        )

        return SuccessResponse(
            message="Événement personnel créé avec succès",
            data=event_schema.model_dump(),
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la création de l'événement: {exc}"
        ) from exc


@router.post("/family", response_model=SuccessResponse, status_code=201)
async def create_family_event(
    event_data: FamilyEventCreateSchema,
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Crée un nouvel événement familial.

    Args:
        event_data: Données de l'événement à créer
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données de l'événement
    """
    try:
        event = service.create_family_event(event_data)

        # Conversion vers le schéma de réponse
        event_schema = EventSchema(
            id=getattr(event, "unique_id", "unknown"),
            event_type=event.event_type,
            date=None,  # TODO: Convertir les dates
            place=event.place,
            reason=event.reason,
            notes=event.notes,
            witnesses=event.witnesses,
            sources=[event.source] if event.source else [],
            person_id=None,
            family_id=event_data.family_id,
        )

        return SuccessResponse(
            message="Événement familial créé avec succès",
            data=event_schema.model_dump(),
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la création de l'événement: {exc}"
        ) from exc


@router.get("/{event_id}", response_model=SuccessResponse)
async def get_event(
    event_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Récupère un événement par son ID.

    Args:
        event_id: Identifiant de l'événement
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les données de l'événement
    """
    try:
        event = service.get_event(event_id)

        if event is None:
            raise HTTPException(
                status_code=404, detail=f"Événement avec l'ID {event_id} non trouvé"
            ) from exc

        # Conversion vers le schéma de réponse
        event_schema = EventSchema(
            id=getattr(event, "unique_id", event_id),
            event_type=event.event_type,
            date=None,  # TODO: Convertir les dates
            place=event.place,
            reason=event.reason,
            notes=event.notes,
            witnesses=event.witnesses,
            sources=[event.source] if event.source else [],
            person_id=getattr(event, "person_id", None),
            family_id=getattr(event, "family_id", None),
        )

        return SuccessResponse(
            message="Événement récupéré avec succès", data=event_schema.model_dump()
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'événement: {exc}",
        ) from exc


@router.put("/{event_id}", response_model=SuccessResponse)
async def update_event(
    event_id: str,
    event_data: EventUpdateSchema,
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Met à jour un événement.

    Args:
        event_id: Identifiant de l'événement
        event_data: Nouvelles données de l'événement
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données mises à jour
    """
    try:
        event = service.update_event(event_id, event_data)

        if event is None:
            raise HTTPException(
                status_code=404, detail=f"Événement avec l'ID {event_id} non trouvé"
            ) from exc

        # Conversion vers le schéma de réponse
        event_schema = EventSchema(
            id=getattr(event, "unique_id", event_id),
            event_type=event.event_type,
            date=None,  # TODO: Convertir les dates
            place=event.place,
            reason=event.reason,
            notes=event.notes,
            witnesses=event.witnesses,
            sources=[event.source] if event.source else [],
            person_id=getattr(event, "person_id", None),
            family_id=getattr(event, "family_id", None),
        )

        return SuccessResponse(
            message="Événement mis à jour avec succès", data=event_schema.model_dump()
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour de l'événement: {exc}",
        ) from exc


@router.delete("/{event_id}", response_model=SuccessResponse)
async def delete_event(
    event_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Supprime un événement.

    Args:
        event_id: Identifiant de l'événement
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès
    """
    try:
        success = service.delete_event(event_id)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Événement avec l'ID {event_id} non trouvé"
            ) from exc

        return SuccessResponse(
            message="Événement supprimé avec succès", data={"event_id": event_id}
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression de l'événement: {exc}",
        ) from exc


@router.get("/", response_model=PaginatedResponse)
async def list_events(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Taille de la page"),
    query: Optional[str] = Query(None, description="Recherche textuelle"),
    event_type: Optional[str] = Query(None, description="Filtrer par type d'événement"),
    person_id: Optional[str] = Query(None, description="Filtrer par personne"),
    family_id: Optional[str] = Query(None, description="Filtrer par famille"),
    year_from: Optional[int] = Query(
        None, ge=1000, le=3000, description="Année minimum"
    ),
    year_to: Optional[int] = Query(None, ge=1000, le=3000, description="Année maximum"),
    place: Optional[str] = Query(None, description="Filtrer par lieu"),
    has_witnesses: Optional[bool] = Query(
        None, description="Filtrer par présence de témoins"
    ),
    has_sources: Optional[bool] = Query(
        None, description="Filtrer par présence de sources"
    ),
    service: GenealogyService = Depends(get_genealogy_service),
) -> PaginatedResponse:
    """
    Liste les événements avec pagination et filtres.

    Args:
        page: Numéro de page
        size: Taille de la page
        query: Recherche textuelle
        event_type: Filtre par type d'événement
        person_id: Filtre par personne
        family_id: Filtre par famille
        year_from: Année minimum
        year_to: Année maximum
        place: Filtre par lieu
        has_witnesses: Filtre par présence de témoins
        has_sources: Filtre par présence de sources
        service: Service de généalogie

    Returns:
        PaginatedResponse: Réponse paginée avec les événements
    """
    try:
        # Construction des paramètres de recherche
        search_params = {
            "page": page,
            "size": size,
            "query": query,
            "event_type": event_type,
            "person_id": person_id,
            "family_id": family_id,
            "place": place,
            "has_witnesses": has_witnesses,
            "has_sources": has_sources,
        }

        # Suppression des valeurs None
        search_params = {k: v for k, v in search_params.items() if v is not None}

        events, total = service.search_events(search_params)

        # Conversion vers les schémas de réponse
        event_schemas = []
        for event in events:
            event_schema = EventSchema(
                id=getattr(event, "unique_id", "unknown"),
                event_type=event.event_type,
                date=None,  # TODO: Convertir les dates
                place=event.place,
                reason=None,  # Pas d'attribut reason dans Event
                notes=event.notes,
                witnesses=event.witnesses,
                sources=[],  # Pas d'attribut sources dans Event
                person_id=getattr(event, "person_id", None),
                family_id=getattr(event, "family_id", None),
            )
            event_schemas.append(event_schema.model_dump())

        # Calcul de la pagination
        total_pages = (total + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        pagination_info = PaginationInfo(
            page=page,
            size=size,
            total=total,
            pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

        return PaginatedResponse(items=event_schemas, pagination=pagination_info)

    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la recherche des événements: {exc}"
        ) from exc


@router.get("/stats/overview", response_model=SuccessResponse)
async def get_event_stats(
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Récupère les statistiques des événements.

    Args:
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les statistiques
    """
    try:
        stats = service.get_stats()

        # Extraction des statistiques d'événements
        event_stats = {
            "total_events": stats.get("total_events", 0),
            "personal_events": stats.get("personal_events", 0),
            "family_events": stats.get("family_events", 0),
            "events_by_type": stats.get("events_by_type", {}),
        }

        return SuccessResponse(
            message="Statistiques des événements récupérées avec succès",
            data=event_stats,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {exc}",
        ) from exc
