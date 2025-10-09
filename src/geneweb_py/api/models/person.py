"""
Schémas Pydantic pour les personnes dans l'API geneweb-py.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from ...core.models import Person, Gender, AccessLevel, Title


class TitleSchema(BaseModel):
    """Schéma pour un titre d'une personne."""

    name: str = Field(..., description="Nom du titre")
    title_type: str = Field("", description="Type de titre")
    place: str = Field("", description="Lieu du titre")
    start_date: Optional[str] = Field(
        None, description="Date de début (format ISO ou GeneWeb)"
    )
    end_date: Optional[str] = Field(
        None, description="Date de fin (format ISO ou GeneWeb)"
    )
    number: int = Field(0, description="Numéro du titre")
    is_main: bool = Field(False, description="Titre principal")


class PersonBaseSchema(BaseModel):
    """Schéma de base pour une personne."""

    first_name: str = Field(..., min_length=1, description="Prénom")
    surname: str = Field(..., min_length=1, description="Nom de famille")
    public_name: Optional[str] = Field(None, description="Nom public")
    titles: List[TitleSchema] = Field(default_factory=list, description="Titres")
    image: Optional[str] = Field(None, description="Image ou photo")
    sex: Union[str, Gender] = Field(..., description="Sexe")
    access_level: Union[str, AccessLevel] = Field(
        "default", description="Niveau d'accès"
    )

    @field_validator("sex", mode="before")
    @classmethod
    def convert_sex(cls, v):
        """Convertit les valeurs de sexe vers les enums internes."""
        if isinstance(v, str):
            mapping = {
                "male": Gender.MALE,
                "female": Gender.FEMALE,
                "unknown": Gender.UNKNOWN,
            }
            return mapping.get(v.lower(), Gender.UNKNOWN)
        return v

    @field_validator("access_level", mode="before")
    @classmethod
    def convert_access_level(cls, v):
        """Convertit les valeurs de niveau d'accès vers les enums internes."""
        if isinstance(v, str):
            mapping = {
                "public": AccessLevel.PUBLIC,
                "private": AccessLevel.PRIVATE,
                "default": AccessLevel.DEFAULT,
            }
            return mapping.get(v.lower(), AccessLevel.DEFAULT)
        return v


class PersonCreateSchema(PersonBaseSchema):
    """Schéma pour la création d'une personne."""

    pass


class PersonUpdateSchema(BaseModel):
    """Schéma pour la mise à jour d'une personne."""

    first_name: Optional[str] = Field(None, min_length=1, description="Prénom")
    surname: Optional[str] = Field(None, min_length=1, description="Nom de famille")
    public_name: Optional[str] = Field(None, description="Nom public")
    titles: Optional[List[TitleSchema]] = Field(None, description="Titres")
    image: Optional[str] = Field(None, description="Image ou photo")
    sex: Optional[Union[str, Gender]] = Field(None, description="Sexe")
    access_level: Optional[Union[str, AccessLevel]] = Field(
        None, description="Niveau d'accès"
    )

    @field_validator("sex", mode="before")
    @classmethod
    def convert_sex(cls, v):
        """Convertit les valeurs de sexe vers les enums internes."""
        if isinstance(v, str):
            mapping = {
                "male": Gender.MALE,
                "female": Gender.FEMALE,
                "unknown": Gender.UNKNOWN,
            }
            return mapping.get(v.lower(), Gender.UNKNOWN)
        return v

    @field_validator("access_level", mode="before")
    @classmethod
    def convert_access_level(cls, v):
        """Convertit les valeurs de niveau d'accès vers les enums internes."""
        if isinstance(v, str):
            mapping = {
                "public": AccessLevel.PUBLIC,
                "private": AccessLevel.PRIVATE,
                "default": AccessLevel.DEFAULT,
            }
            return mapping.get(v.lower(), AccessLevel.DEFAULT)
        return v


class PersonSchema(PersonBaseSchema):
    """Schéma complet pour une personne."""

    id: str = Field(..., description="Identifiant unique de la personne")
    birth_date: Optional[str] = Field(None, description="Date de naissance")
    birth_place: Optional[str] = Field(None, description="Lieu de naissance")
    death_date: Optional[str] = Field(None, description="Date de décès")
    death_place: Optional[str] = Field(None, description="Lieu de décès")
    death_cause: Optional[str] = Field(None, description="Cause du décès")
    burial_date: Optional[str] = Field(None, description="Date d'inhumation")
    burial_place: Optional[str] = Field(None, description="Lieu d'inhumation")
    baptism_date: Optional[str] = Field(None, description="Date de baptême")
    baptism_place: Optional[str] = Field(None, description="Lieu de baptême")
    notes: List[str] = Field(default_factory=list, description="Notes personnelles")
    sources: List[str] = Field(default_factory=list, description="Sources")
    families: List[str] = Field(default_factory=list, description="IDs des familles")
    events: List[str] = Field(
        default_factory=list, description="IDs des événements personnels"
    )

    class Config:
        """Configuration Pydantic."""

        from_attributes = True


class PersonListSchema(BaseModel):
    """Schéma pour la liste des personnes."""

    id: str = Field(..., description="Identifiant unique")
    first_name: str = Field(..., description="Prénom")
    surname: str = Field(..., description="Nom de famille")
    public_name: Optional[str] = Field(None, description="Nom public")
    birth_date: Optional[str] = Field(None, description="Date de naissance")
    death_date: Optional[str] = Field(None, description="Date de décès")
    sex: Gender = Field(..., description="Sexe")
    access_level: AccessLevel = Field(..., description="Niveau d'accès")


class PersonSearchSchema(BaseModel):
    """Schéma pour la recherche de personnes."""

    query: Optional[str] = Field(None, description="Recherche textuelle")
    first_name: Optional[str] = Field(None, description="Filtrer par prénom")
    surname: Optional[str] = Field(None, description="Filtrer par nom de famille")
    sex: Optional[Gender] = Field(None, description="Filtrer par sexe")
    birth_year_from: Optional[int] = Field(
        None, ge=1000, le=3000, description="Année de naissance minimum"
    )
    birth_year_to: Optional[int] = Field(
        None, ge=1000, le=3000, description="Année de naissance maximum"
    )
    death_year_from: Optional[int] = Field(
        None, ge=1000, le=3000, description="Année de décès minimum"
    )
    death_year_to: Optional[int] = Field(
        None, ge=1000, le=3000, description="Année de décès maximum"
    )
    place: Optional[str] = Field(None, description="Filtrer par lieu")
    access_level: Optional[AccessLevel] = Field(
        None, description="Filtrer par niveau d'accès"
    )
    page: int = Field(1, ge=1, description="Numéro de page")
    size: int = Field(20, ge=1, le=100, description="Taille de la page")


class PersonStatsSchema(BaseModel):
    """Schéma pour les statistiques des personnes."""

    total: int = Field(..., ge=0, description="Nombre total de personnes")
    by_sex: Dict[str, int] = Field(..., description="Répartition par sexe")
    by_access_level: Dict[str, int] = Field(
        ..., description="Répartition par niveau d'accès"
    )
    by_century: Dict[str, int] = Field(
        ..., description="Répartition par siècle de naissance"
    )
    with_birth_date: int = Field(..., ge=0, description="Nombre avec date de naissance")
    with_death_date: int = Field(..., ge=0, description="Nombre avec date de décès")
