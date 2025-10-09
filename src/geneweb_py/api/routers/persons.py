"""
Router FastAPI pour la gestion des personnes dans l'API geneweb-py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_genealogy_service
from ..models.person import (
    PersonCreateSchema,
    PersonListSchema,
    PersonSchema,
    PersonSearchSchema,
    PersonStatsSchema,
    PersonUpdateSchema,
)
from ..models.responses import (
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
)
from ..services.genealogy_service import GenealogyService

router = APIRouter()


@router.post("/", response_model=SuccessResponse, status_code=201)
async def create_person(
    person_data: PersonCreateSchema,
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Crée une nouvelle personne.

    Args:
        person_data: Données de la personne à créer
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données de la personne
    """
    try:
        person = service.create_person(person_data)

        # Conversion vers le schéma de réponse
        person_schema = PersonSchema(
            id=person.unique_id,
            first_name=person.first_name,
            surname=person.last_name,
            public_name=person.public_name,
            titles=[],  # TODO: Convertir les titres
            image=person.image_path,
            sex=person.gender,
            access_level=person.access_level,
            birth_date=None,  # TODO: Convertir les dates
            birth_place=person.birth_place,
            death_date=None,  # TODO: Convertir les dates
            death_place=person.death_place,
            death_cause=None,
            burial_date=None,  # TODO: Convertir les dates
            burial_place=person.burial_place,
            baptism_date=None,  # TODO: Convertir les dates
            baptism_place=person.baptism_place,
            notes=person.notes,
            sources=[],  # TODO: Récupérer les sources
            families=[],  # TODO: Récupérer les familles
            events=[],  # TODO: Récupérer les événements
        )

        return SuccessResponse(
            message="Personne créée avec succès", data=person_schema.model_dump()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la création de la personne: {exc}"
        ) from exc


@router.get("/{person_id}", response_model=SuccessResponse)
async def get_person(
    person_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Récupère une personne par son ID.

    Args:
        person_id: Identifiant de la personne
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données de la personne
    """
    person = service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404, detail=f"Personne avec l'ID '{person_id}' non trouvée"
        ) from exc

    # Conversion vers le schéma de réponse
    person_schema = PersonSchema(
        id=person.unique_id,
        first_name=person.first_name,
        surname=person.last_name,
        public_name=person.public_name,
        titles=[],  # TODO: Convertir les titres
        image=person.image_path,
        sex=person.gender,
        access_level=person.access_level,
        birth_date=None,  # TODO: Convertir les dates
        birth_place=person.birth_place,
        death_date=None,  # TODO: Convertir les dates
        death_place=person.death_place,
        death_cause=None,
        burial_date=None,  # TODO: Convertir les dates
        burial_place=person.burial_place,
        baptism_date=None,  # TODO: Convertir les dates
        baptism_place=person.baptism_place,
        notes=person.notes,
        sources=[],  # TODO: Récupérer les sources
        families=[],  # TODO: Récupérer les familles
        events=[],  # TODO: Récupérer les événements
    )

    return SuccessResponse(
        message="Personne récupérée avec succès", data=person_schema.model_dump()
    )


@router.put("/{person_id}", response_model=SuccessResponse)
async def update_person(
    person_id: str,
    person_data: PersonUpdateSchema,
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Met à jour une personne.

    Args:
        person_id: Identifiant de la personne
        person_data: Nouvelles données de la personne
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès avec les données mises à jour
    """
    person = service.update_person(person_id, person_data)

    if person is None:
        raise HTTPException(
            status_code=404, detail=f"Personne avec l'ID '{person_id}' non trouvée"
        ) from exc

    # Conversion vers le schéma de réponse
    person_schema = PersonSchema(
        id=person.unique_id,
        first_name=person.first_name,
        surname=person.last_name,
        public_name=person.public_name,
        titles=[],  # TODO: Convertir les titres
        image=person.image_path,
        sex=person.gender,
        access_level=person.access_level,
        birth_date=None,  # TODO: Convertir les dates
        birth_place=person.birth_place,
        death_date=None,  # TODO: Convertir les dates
        death_place=person.death_place,
        death_cause=None,
        burial_date=None,  # TODO: Convertir les dates
        burial_place=person.burial_place,
        baptism_date=None,  # TODO: Convertir les dates
        baptism_place=person.baptism_place,
        notes=person.notes,
        sources=[],  # TODO: Récupérer les sources
        families=[],  # TODO: Récupérer les familles
        events=[],  # TODO: Récupérer les événements
    )

    return SuccessResponse(
        message="Personne mise à jour avec succès", data=person_schema.model_dump()
    )


@router.delete("/{person_id}", response_model=SuccessResponse)
async def delete_person(
    person_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Supprime une personne.

    Args:
        person_id: Identifiant de la personne
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse de succès
    """
    success = service.delete_person(person_id)

    if not success:
        raise HTTPException(
            status_code=404, detail=f"Personne avec l'ID '{person_id}' non trouvée"
        ) from exc

    return SuccessResponse(message="Personne supprimée avec succès")


@router.get("/", response_model=PaginatedResponse)
async def list_persons(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Taille de la page"),
    query: Optional[str] = Query(None, description="Recherche textuelle"),
    first_name: Optional[str] = Query(None, description="Filtrer par prénom"),
    surname: Optional[str] = Query(None, description="Filtrer par nom de famille"),
    sex: Optional[str] = Query(None, description="Filtrer par sexe"),
    access_level: Optional[str] = Query(None, description="Filtrer par niveau d'accès"),
    service: GenealogyService = Depends(get_genealogy_service),
) -> PaginatedResponse:
    """
    Liste les personnes avec pagination et filtres.

    Args:
        page: Numéro de page
        size: Taille de la page
        query: Recherche textuelle
        first_name: Filtre par prénom
        surname: Filtre par nom de famille
        sex: Filtre par sexe
        access_level: Filtre par niveau d'accès
        service: Service de généalogie

    Returns:
        PaginatedResponse: Réponse paginée avec les personnes
    """
    # Construction des paramètres de recherche
    search_params = PersonSearchSchema(
        page=page,
        size=size,
        query=query,
        first_name=first_name,
        surname=surname,
        sex=sex,  # TODO: Conversion depuis string
        access_level=access_level,  # TODO: Conversion depuis string
        birth_year_from=None,
        birth_year_to=None,
        death_year_from=None,
        death_year_to=None,
        place=None,
    )

    persons, total = service.search_persons(search_params)

    # Conversion vers les schémas de liste
    person_list = []
    for person in persons:
        person_schema = PersonListSchema(
            id=person.unique_id,
            first_name=person.first_name,
            surname=person.last_name,
            public_name=person.public_name,
            birth_date=None,  # TODO: Convertir les dates
            death_date=None,
            sex=person.gender,
            access_level=person.access_level,
        )
        person_list.append(person_schema.model_dump())

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

    return PaginatedResponse(items=person_list, pagination=pagination)


@router.get("/{person_id}/families", response_model=SuccessResponse)
async def get_person_families(
    person_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Récupère les familles d'une personne.

    Args:
        person_id: Identifiant de la personne
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les familles de la personne
    """
    person = service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404, detail=f"Personne avec l'ID '{person_id}' non trouvée"
        ) from exc

    # TODO: Implémenter la récupération des familles de la personne
    families = []

    return SuccessResponse(message="Familles récupérées avec succès", data=families)


@router.get("/{person_id}/events", response_model=SuccessResponse)
async def get_person_events(
    person_id: str, service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Récupère les événements d'une personne.

    Args:
        person_id: Identifiant de la personne
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les événements de la personne
    """
    person = service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404, detail=f"Personne avec l'ID '{person_id}' non trouvée"
        ) from exc

    # TODO: Implémenter la récupération des événements de la personne
    events = []

    return SuccessResponse(message="Événements récupérés avec succès", data=events)


@router.get("/stats/overview", response_model=SuccessResponse)
async def get_person_stats(
    service: GenealogyService = Depends(get_genealogy_service),
) -> SuccessResponse:
    """
    Récupère les statistiques des personnes.

    Args:
        service: Service de généalogie

    Returns:
        SuccessResponse: Réponse avec les statistiques
    """
    stats = service.get_stats()

    person_stats = PersonStatsSchema(
        total=stats["total_persons"],
        by_sex=stats["persons_by_sex"],
        by_access_level=stats["persons_by_access_level"],
        by_century={},  # TODO: Calculer par siècle
        with_birth_date=stats["persons_with_birth_date"],
        with_death_date=stats["persons_with_death_date"],
    )

    return SuccessResponse(
        message="Statistiques récupérées avec succès", data=person_stats.model_dump()
    )
