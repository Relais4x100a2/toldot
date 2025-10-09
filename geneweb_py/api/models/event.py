"""
Schémas Pydantic pour les événements dans l'API geneweb-py.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

from ...core.models import Event, EventType, FamilyEventType


class EventBaseSchema(BaseModel):
    """Schéma de base pour un événement."""

    event_type: Union[EventType, FamilyEventType] = Field(
        ..., description="Type d'événement"
    )
    date: Optional[str] = Field(None, description="Date de l'événement")
    place: Optional[str] = Field(None, description="Lieu de l'événement")
    reason: Optional[str] = Field(None, description="Raison ou cause")
    note: Optional[str] = Field(None, description="Note sur l'événement")
    witnesses: List[str] = Field(default_factory=list, description="Témoins")
    sources: List[str] = Field(default_factory=list, description="Sources")

    @field_validator("event_type", mode="before")
    @classmethod
    def convert_event_type(cls, v):
        """Convertit les types d'événements lisibles vers les enums internes."""
        if isinstance(v, str):
            # Mapping pour les événements personnels
            personal_mapping = {
                "birth": EventType.BIRTH,
                "baptism": EventType.BAPTISM,
                "death": EventType.DEATH,
                "burial": EventType.BURIAL,
                "cremation": EventType.CREMATION,
                "confirmation": EventType.CONFIRMATION,
                "first_communion": EventType.FIRST_COMMUNION,
                "ordination": EventType.ORDINATION,
                "excommunication": EventType.EXCOMMUNICATION,
                "naturalization": EventType.NATURALIZATION,
                "occupation": EventType.OCCUPATION,
                "residence": EventType.RESIDENCE,
                "education": EventType.EDUCATION,
                "graduation": EventType.GRADUATION,
                "military_service": EventType.MILITARY_SERVICE,
                "marriage": EventType.MARRIAGE,
                "divorce": EventType.DIVORCE,
                "separation": EventType.SEPARATION,
                "engagement": EventType.ENGAGEMENT,
                "pacs": EventType.PACS,
            }

            # Mapping pour les événements familiaux
            family_mapping = {
                "marriage": FamilyEventType.MARRIAGE,
                "divorce": FamilyEventType.DIVORCE,
                "separation": FamilyEventType.SEPARATION,
                "engagement": FamilyEventType.ENGAGEMENT,
                "pacs": FamilyEventType.PACS,
            }

            # Essayer d'abord les événements personnels
            if v in personal_mapping:
                return personal_mapping[v]
            # Puis les événements familiaux
            elif v in family_mapping:
                return family_mapping[v]
            # Sinon, essayer de trouver par valeur enum
            else:
                for event_type in EventType:
                    if event_type.value == v:
                        return event_type
                for event_type in FamilyEventType:
                    if event_type.value == v:
                        return event_type

        return v


class PersonalEventCreateSchema(EventBaseSchema):
    """Schéma pour la création d'un événement personnel."""

    person_id: str = Field(..., description="Identifiant de la personne")
    event_type: EventType = Field(..., description="Type d'événement personnel")


class FamilyEventCreateSchema(EventBaseSchema):
    """Schéma pour la création d'un événement familial."""

    family_id: str = Field(..., description="Identifiant de la famille")
    event_type: FamilyEventType = Field(..., description="Type d'événement familial")


class EventUpdateSchema(BaseModel):
    """Schéma pour la mise à jour d'un événement."""

    event_type: Optional[Union[EventType, FamilyEventType]] = Field(
        None, description="Type d'événement"
    )
    date: Optional[str] = Field(None, description="Date de l'événement")
    place: Optional[str] = Field(None, description="Lieu de l'événement")
    reason: Optional[str] = Field(None, description="Raison ou cause")
    note: Optional[str] = Field(None, description="Note sur l'événement")
    witnesses: Optional[List[str]] = Field(None, description="Témoins")
    sources: Optional[List[str]] = Field(None, description="Sources")


class EventSchema(EventBaseSchema):
    """Schéma complet pour un événement."""

    id: str = Field(..., description="Identifiant unique de l'événement")
    person_id: Optional[str] = Field(
        None, description="Identifiant de la personne (pour événements personnels)"
    )
    family_id: Optional[str] = Field(
        None, description="Identifiant de la famille (pour événements familiaux)"
    )

    class Config:
        """Configuration Pydantic."""

        from_attributes = True


class EventListSchema(BaseModel):
    """Schéma pour la liste des événements."""

    id: str = Field(..., description="Identifiant unique")
    event_type: Union[EventType, FamilyEventType] = Field(
        ..., description="Type d'événement"
    )
    date: Optional[str] = Field(None, description="Date de l'événement")
    place: Optional[str] = Field(None, description="Lieu de l'événement")
    person_id: Optional[str] = Field(None, description="Identifiant de la personne")
    family_id: Optional[str] = Field(None, description="Identifiant de la famille")


class EventSearchSchema(BaseModel):
    """Schéma pour la recherche d'événements."""

    query: Optional[str] = Field(None, description="Recherche textuelle")
    event_type: Optional[Union[EventType, FamilyEventType]] = Field(
        None, description="Filtrer par type d'événement"
    )
    person_id: Optional[str] = Field(None, description="Filtrer par personne")
    family_id: Optional[str] = Field(None, description="Filtrer par famille")
    year_from: Optional[int] = Field(
        None, ge=1000, le=3000, description="Année minimum"
    )
    year_to: Optional[int] = Field(None, ge=1000, le=3000, description="Année maximum")
    place: Optional[str] = Field(None, description="Filtrer par lieu")
    has_witnesses: Optional[bool] = Field(
        None, description="Filtrer par présence de témoins"
    )
    has_sources: Optional[bool] = Field(
        None, description="Filtrer par présence de sources"
    )
    page: int = Field(1, ge=1, description="Numéro de page")
    size: int = Field(20, ge=1, le=100, description="Taille de la page")


class EventStatsSchema(BaseModel):
    """Schéma pour les statistiques des événements."""

    total: int = Field(..., ge=0, description="Nombre total d'événements")
    by_type: Dict[str, int] = Field(..., description="Répartition par type d'événement")
    by_century: Dict[str, int] = Field(..., description="Répartition par siècle")
    with_date: int = Field(..., ge=0, description="Nombre avec date")
    with_place: int = Field(..., ge=0, description="Nombre avec lieu")
    with_witnesses: int = Field(..., ge=0, description="Nombre avec témoins")
    with_sources: int = Field(..., ge=0, description="Nombre avec sources")
    personal_events: int = Field(
        ..., ge=0, description="Nombre d'événements personnels"
    )
    family_events: int = Field(..., ge=0, description="Nombre d'événements familiaux")
