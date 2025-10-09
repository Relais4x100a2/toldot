"""
Dépendances FastAPI pour l'API geneweb-py.

Ce module fournit les dépendances communes utilisées dans les routers
pour l'injection de dépendances et la gestion des services.
"""

from contextlib import asynccontextmanager
from typing import Generator, Tuple

from fastapi import Depends, HTTPException, status

from .services.genealogy_service import GenealogyService


def get_genealogy_service() -> GenealogyService:
    """
    Dépendance pour obtenir le service de généalogie.

    Returns:
        GenealogyService: Service de généalogie
    """
    # Import ici pour éviter les imports circulaires
    from .main import get_global_genealogy_service

    return get_global_genealogy_service()


@asynccontextmanager
async def get_genealogy_service_context() -> Generator[GenealogyService, None, None]:
    """
    Contexte asynchrone pour le service de généalogie.

    Yields:
        GenealogyService: Service de généalogie
    """
    try:
        service = get_genealogy_service()
        yield service
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur du service de généalogie: {exc}",
        ) from exc


def validate_genealogy_loaded(
    service: GenealogyService = Depends(get_genealogy_service),
) -> GenealogyService:
    """
    Valide qu'une généalogie est chargée dans le service.

    Args:
        service: Service de généalogie

    Returns:
        GenealogyService: Service de généalogie validé

    Raises:
        HTTPException: Si aucune généalogie n'est chargée
    """
    try:
        # Tentative d'accès à la généalogie pour vérifier qu'elle est chargée
        _ = service.genealogy
        return service
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucune généalogie n'est chargée. Utilisez l'endpoint /api/v1/genealogy/import pour charger un fichier.",
        ) from exc


def get_pagination_params(
    page: int = 1, size: int = 20, max_size: int = 100
) -> Tuple[int, int]:
    """
    Valide et retourne les paramètres de pagination.

    Args:
        page: Numéro de page
        size: Taille de la page
        max_size: Taille maximum autorisée

    Returns:
        tuple[int, int]: (page, size) validés

    Raises:
        HTTPException: Si les paramètres sont invalides
    """
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
    """
    Valide et retourne la limite de recherche.

    Args:
        limit: Limite demandée
        max_limit: Limite maximum autorisée

    Returns:
        int: Limite validée

    Raises:
        HTTPException: Si la limite est invalide
    """
    if limit < 1 or limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La limite doit être entre 1 et {max_limit}",
        )

    return limit
