"""
Schémas de réponse standardisés pour l'API geneweb-py.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Détail d'une erreur."""

    field: Optional[str] = Field(None, description="Champ concerné par l'erreur")
    message: str = Field(..., description="Message d'erreur")
    code: Optional[str] = Field(None, description="Code d'erreur")


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""

    error: bool = Field(True, description="Indique qu'il s'agit d'une erreur")
    message: str = Field(..., description="Message d'erreur principal")
    details: Optional[List[ErrorDetail]] = Field(
        None, description="Détails des erreurs"
    )
    code: Optional[str] = Field(None, description="Code d'erreur HTTP")


class SuccessResponse(BaseModel):
    """Réponse de succès standardisée."""

    success: bool = Field(True, description="Indique que l'opération a réussi")
    message: str = Field(..., description="Message de succès")
    data: Optional[Any] = Field(None, description="Données retournées")


class PaginationInfo(BaseModel):
    """Informations de pagination."""

    page: int = Field(..., ge=1, description="Numéro de page")
    size: int = Field(..., ge=1, le=100, description="Taille de la page")
    total: int = Field(..., ge=0, description="Nombre total d'éléments")
    pages: int = Field(..., ge=0, description="Nombre total de pages")
    has_next: bool = Field(..., description="Indique s'il y a une page suivante")
    has_prev: bool = Field(..., description="Indique s'il y a une page précédente")


class PaginatedResponse(BaseModel):
    """Réponse paginée."""

    items: List[Any] = Field(..., description="Éléments de la page")
    pagination: PaginationInfo = Field(..., description="Informations de pagination")


class HealthResponse(BaseModel):
    """Réponse de vérification de santé."""

    status: str = Field(..., description="Statut de l'API")
    message: str = Field(..., description="Message de statut")
    version: str = Field(..., description="Version de l'API")


class StatsResponse(BaseModel):
    """Réponse de statistiques."""

    total_persons: int = Field(..., ge=0, description="Nombre total de personnes")
    total_families: int = Field(..., ge=0, description="Nombre total de familles")
    total_events: int = Field(..., ge=0, description="Nombre total d'événements")
    persons_by_sex: Dict[str, int] = Field(
        default_factory=dict, description="Répartition par sexe"
    )
    persons_by_access_level: Dict[str, int] = Field(
        default_factory=dict, description="Répartition par niveau d'accès"
    )
    persons_by_birth_century: Dict[str, int] = Field(
        default_factory=dict,
        description="Répartition des personnes par siècle de naissance",
    )
    families_by_status: Dict[str, int] = Field(
        default_factory=dict, description="Répartition des familles par statut"
    )
    families_by_marriage_century: Dict[str, int] = Field(
        default_factory=dict,
        description="Répartition des familles par siècle de mariage",
    )
    events_by_type: Dict[str, int] = Field(
        default_factory=dict, description="Répartition des événements par type"
    )
    events_by_century: Dict[str, int] = Field(
        default_factory=dict, description="Répartition des événements par siècle"
    )
    average_children_per_family: float = Field(
        0.0, ge=0, description="Nombre moyen d'enfants par famille"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Métadonnées (fichier source, encodage, dates)"
    )
    persons_with_birth_date: int = Field(
        0, ge=0, description="Nombre de personnes avec date de naissance"
    )
    persons_with_death_date: int = Field(
        0, ge=0, description="Nombre de personnes avec date de décès"
    )
    families_with_children: int = Field(
        0, ge=0, description="Nombre de familles ayant au moins un enfant"
    )
    personal_events: int = Field(0, ge=0, description="Nombre d'événements personnels")
    family_events: int = Field(0, ge=0, description="Nombre d'événements familiaux")
    families_with_marriage_date: int = Field(
        0, ge=0, description="Familles avec date de mariage renseignée"
    )
    families_with_divorce_date: int = Field(
        0, ge=0, description="Familles avec date de divorce renseignée"
    )
    advanced: Optional[Dict[str, Any]] = Field(
        None,
        description="Statistiques avancées (longévité, géographie, tailles de famille)",
    )
