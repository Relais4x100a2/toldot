"""
Router FastAPI pour la gestion des familles dans l'API geneweb-py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_genealogy_service
from ..models.family import (
    FamilyCreateSchema,
    FamilyListSchema,
    FamilySchema,
    FamilySearchSchema,
    FamilyStatsSchema,
    FamilyUpdateSchema,
)
from ..models.responses import (
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
)
from ..services.genealogy_service import GenealogyService

router = APIRouter()


@router.post("/", response_model=SuccessResponse, status_code=201)
async def create_family(
    family_data: FamilyCreateSchema,
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Crée une nouvelle famille.

    Args:
        family_data: Données de la famille à créer
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données de la famille
    """
    try:
        family = service.create_family(family_data)

        # Conversion vers le schéma de réponse
        family_schema = FamilySchema(
            id=family.family_id,
            husband_id=family.husband_id,
            wife_id=family.wife_id,
            children=[],  # TODO: Convertir les enfants
            marriage_status=family.marriage_status,
            notes=family.comments,
            sources=[family.family_source] if family.family_source else [],
            marriage_date=None,  # TODO: Convertir les dates
            marriage_place=None,
            divorce_date=None,
            divorce_place=None,
            events=[],  # TODO: Récupérer les événements
        )

        return SuccessResponse(
            message="Famille créée avec succès", data=family_schema.model_dump()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la création de la famille: {exc}"
        )


@router.get("/{family_id}", response_model=SuccessResponse)
async def get_family(
    family_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Récupère une famille par son ID.

    Args:
        family_id: Identifiant de la famille
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données de la famille
    """
    family = service.get_family(family_id)

    if family is None:
        raise HTTPException(
            status_code=404, detail=f"Famille avec l'ID '{family_id}' non trouvée"
        )

    # Conversion vers le schéma de réponse
    family_schema = FamilySchema(
        id=family.family_id,
        husband_id=family.husband_id,
        wife_id=family.wife_id,
        children=[],  # TODO: Convertir les enfants
        marriage_status=family.marriage_status,
        notes=family.comments,
        sources=[family.family_source] if family.family_source else [],
        marriage_date=None,  # TODO: Convertir les dates
        marriage_place=None,
        divorce_date=None,
        divorce_place=None,
        events=[],  # TODO: Récupérer les événements
    )

    return SuccessResponse(
        message="Famille récupérée avec succès", data=family_schema.model_dump()
    )


@router.put("/{family_id}", response_model=SuccessResponse)
async def update_family(
    family_id: str,
    family_data: FamilyUpdateSchema,
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Met à jour une famille.

    Args:
        family_id: Identifiant de la famille
        family_data: Nouvelles données de la famille
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données mises à jour
    """
    family = service.update_family(family_id, family_data)

    if family is None:
        raise HTTPException(
            status_code=404, detail=f"Famille avec l'ID '{family_id}' non trouvée"
        )

    # Conversion vers le schéma de réponse
    family_schema = FamilySchema(
        id=family.family_id,
        husband_id=family.husband_id,
        wife_id=family.wife_id,
        children=[],  # TODO: Convertir les enfants
        marriage_status=family.marriage_status,
        notes=family.comments,
        sources=[family.family_source] if family.family_source else [],
        marriage_date=None,  # TODO: Convertir les dates
        marriage_place=None,
        divorce_date=None,
        divorce_place=None,
        events=[],  # TODO: Récupérer les événements
    )

    return SuccessResponse(
        message="Famille mise à jour avec succès", data=family_schema.model_dump()
    )


@router.delete("/{family_id}", response_model=SuccessResponse)
async def delete_family(
    family_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Supprime une famille.

    Args:
        family_id: Identifiant de la famille
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès
    """
    success = service.delete_family(family_id)

    if not success:
        raise HTTPException(
            status_code=404, detail=f"Famille avec l'ID '{family_id}' non trouvée"
        )

    return SuccessResponse(message="Famille supprimée avec succès")


@router.get("/", response_model=PaginatedResponse)
async def list_families(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Taille de la page"),
    query: Optional[str] = Query(None, description="Recherche textuelle"),
    husband_id: Optional[str] = Query(None, description="Filtrer par mari"),
    wife_id: Optional[str] = Query(None, description="Filtrer par épouse"),
    marriage_status: Optional[str] = Query(
        None, description="Filtrer par statut de mariage"
    ),
    has_children: Optional[bool] = Query(
        None, description="Filtrer par présence d'enfants"
    ),
    min_children: Optional[int] = Query(
        None, ge=0, description="Nombre minimum d'enfants"
    ),
    max_children: Optional[int] = Query(
        None, ge=0, description="Nombre maximum d'enfants"
    ),
    service: GenealogyService = Depends(get_genealogy_service),
) -> PaginatedResponse:
    """
    Liste les familles avec pagination et filtres.

    Args:
        page: Numéro de page
        size: Taille de la page
        query: Recherche textuelle
        husband_id: Filtre par mari
        wife_id: Filtre par épouse
        marriage_status: Filtre par statut de mariage
        has_children: Filtre par présence d'enfants
        min_children: Nombre minimum d'enfants
        max_children: Nombre maximum d'enfants
        service: Service de généalogie

    Returns:
        PaginatedResponse: Réponse paginée avec les familles
    """
    # Construction des paramètres de recherche
    search_params = FamilySearchSchema(
        page=page,
        size=size,
        query=query,
        husband_id=husband_id,
        wife_id=wife_id,
        marriage_status=marriage_status,  # TODO: Conversion depuis string
        marriage_year_from=None,
        marriage_year_to=None,
        divorce_year_from=None,
        divorce_year_to=None,
        place=None,
        has_children=has_children,
        min_children=min_children,
        max_children=max_children,
    )

    families, total = service.search_families(search_params)

    # Conversion vers les schémas de liste
    family_list = []
    for family in families:
        family_schema = FamilyListSchema(
            id=family.family_id,
            husband_id=family.husband_id,
            wife_id=family.wife_id,
            children_count=len(family.children),
            marriage_date=None,  # TODO: Convertir les dates
            marriage_status=family.marriage_status,
        )
        family_list.append(family_schema.model_dump())

    # Calcul de la pagination
    total_pages = (total + size - 1) // size
    has_next = page < total_pages
    has_prev = page > 1

    pagination = PaginationInfo(
        page=page,
        size=size,
        total=total,
        pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
    )

    return PaginatedResponse(items=family_list, pagination=pagination)


@router.get("/{family_id}/children", response_model=SuccessResponse)
async def get_family_children(
    family_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Récupère les enfants d'une famille.

    Args:
        family_id: Identifiant de la famille
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les enfants de la famille
    """
    family = service.get_family(family_id)

    if family is None:
        raise HTTPException(
            status_code=404, detail=f"Famille avec l'ID '{family_id}' non trouvée"
        )

    # TODO: Implémenter la récupération des enfants avec leurs détails
    children = []

    return SuccessResponse(message="Enfants récupérés avec succès", data=children)


@router.get("/{family_id}/events", response_model=SuccessResponse)
async def get_family_events(
    family_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Récupère les événements d'une famille.

    Args:
        family_id: Identifiant de la famille
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les événements de la famille
    """
    try:
        family = service.get_family(family_id)

        if family is None:
            raise HTTPException(
                status_code=404, detail=f"Famille avec l'ID '{family_id}' non trouvée"
            )

        # Conversion des événements familiaux
        events = []
        for event in family.events:
            event_data = {
                "id": getattr(event, "unique_id", "unknown"),
                "event_type": event.event_type.value if event.event_type else None,
                "date": None,  # TODO: Convertir les dates
                "place": event.place,
                "reason": event.reason,
                "notes": event.notes,
                "witnesses": event.witnesses,
                "sources": event.sources,
                "family_id": family_id,
            }
            events.append(event_data)

        return SuccessResponse(message="Événements récupérés avec succès", data=events)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des événements: {exc}",
        )


@router.get("/stats/overview", response_model=SuccessResponse)
async def get_family_stats(
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Récupère les statistiques des familles.

    Args:
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les statistiques
    """
    stats = service.get_stats()

    family_stats = FamilyStatsSchema(
        total=stats["total_families"],
        by_status=stats["families_by_status"],
        by_century={},  # TODO: Calculer par siècle
        with_marriage_date=0,  # TODO: Calculer
        with_divorce_date=0,  # TODO: Calculer
        average_children=stats["average_children_per_family"],
        families_with_children=stats["families_with_children"],
    )

    return SuccessResponse(
        message="Statistiques récupérées avec succès", data=family_stats.model_dump()
    )
