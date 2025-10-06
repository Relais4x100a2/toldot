"""
Schémas Pydantic pour les familles dans l'API geneweb-py.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

from ...core.models import Family, MarriageStatus, ChildSex


class ChildSchema(BaseModel):
    """Schéma pour un enfant dans une famille."""
    
    person_id: str = Field(..., description="Identifiant de la personne")
    sex: Union[str, ChildSex] = Field("unknown", description="Sexe de l'enfant")
    last_name: Optional[str] = Field(None, description="Nom de famille si différent du père")
    
    @field_validator('sex', mode='before')
    @classmethod
    def convert_sex(cls, v):
        """Convertit les valeurs de sexe vers les enums internes."""
        if isinstance(v, str):
            mapping = {
                "male": ChildSex.MALE,
                "female": ChildSex.FEMALE,
                "unknown": ChildSex.UNKNOWN
            }
            return mapping.get(v.lower(), ChildSex.UNKNOWN)
        return v


class FamilyBaseSchema(BaseModel):
    """Schéma de base pour une famille."""
    
    husband_id: Optional[str] = Field(None, description="Identifiant du mari")
    wife_id: Optional[str] = Field(None, description="Identifiant de l'épouse")
    children: List[ChildSchema] = Field(default_factory=list, description="Enfants")
    marriage_status: Union[str, MarriageStatus] = Field("married", description="Statut du mariage")
    notes: List[str] = Field(default_factory=list, description="Notes familiales")
    sources: List[str] = Field(default_factory=list, description="Sources")
    
    @field_validator('marriage_status', mode='before')
    @classmethod
    def convert_marriage_status(cls, v):
        """Convertit les valeurs de statut de mariage vers les enums internes."""
        if isinstance(v, str):
            mapping = {
                "married": MarriageStatus.MARRIED,
                "divorced": MarriageStatus.DIVORCED,
                "separated": MarriageStatus.SEPARATED,
                "widowed": MarriageStatus.WIDOWED,
                "unknown": MarriageStatus.UNKNOWN
            }
            return mapping.get(v.lower(), MarriageStatus.MARRIED)
        return v


class FamilyCreateSchema(FamilyBaseSchema):
    """Schéma pour la création d'une famille."""
    pass


class FamilyUpdateSchema(BaseModel):
    """Schéma pour la mise à jour d'une famille."""
    
    husband_id: Optional[str] = Field(None, description="Identifiant du mari")
    wife_id: Optional[str] = Field(None, description="Identifiant de l'épouse")
    children: Optional[List[ChildSchema]] = Field(None, description="Enfants")
    marriage_status: Optional[Union[str, MarriageStatus]] = Field(None, description="Statut du mariage")
    notes: Optional[List[str]] = Field(None, description="Notes familiales")
    sources: Optional[List[str]] = Field(None, description="Sources")
    
    @field_validator('marriage_status', mode='before')
    @classmethod
    def convert_marriage_status(cls, v):
        """Convertit les valeurs de statut de mariage vers les enums internes."""
        if isinstance(v, str):
            mapping = {
                "married": MarriageStatus.MARRIED,
                "divorced": MarriageStatus.DIVORCED,
                "separated": MarriageStatus.SEPARATED,
                "widowed": MarriageStatus.WIDOWED,
                "unknown": MarriageStatus.UNKNOWN
            }
            return mapping.get(v.lower(), MarriageStatus.MARRIED)
        return v


class FamilySchema(FamilyBaseSchema):
    """Schéma complet pour une famille."""
    
    id: str = Field(..., description="Identifiant unique de la famille")
    marriage_date: Optional[str] = Field(None, description="Date de mariage")
    marriage_place: Optional[str] = Field(None, description="Lieu de mariage")
    divorce_date: Optional[str] = Field(None, description="Date de divorce")
    divorce_place: Optional[str] = Field(None, description="Lieu de divorce")
    events: List[str] = Field(default_factory=list, description="IDs des événements familiaux")
    
    class Config:
        """Configuration Pydantic."""
        from_attributes = True


class FamilyListSchema(BaseModel):
    """Schéma pour la liste des familles."""
    
    id: str = Field(..., description="Identifiant unique")
    husband_id: Optional[str] = Field(None, description="Identifiant du mari")
    wife_id: Optional[str] = Field(None, description="Identifiant de l'épouse")
    children_count: int = Field(..., ge=0, description="Nombre d'enfants")
    marriage_date: Optional[str] = Field(None, description="Date de mariage")
    marriage_status: MarriageStatus = Field(..., description="Statut du mariage")


class FamilySearchSchema(BaseModel):
    """Schéma pour la recherche de familles."""
    
    query: Optional[str] = Field(None, description="Recherche textuelle")
    husband_id: Optional[str] = Field(None, description="Filtrer par mari")
    wife_id: Optional[str] = Field(None, description="Filtrer par épouse")
    marriage_status: Optional[MarriageStatus] = Field(None, description="Filtrer par statut de mariage")
    marriage_year_from: Optional[int] = Field(None, ge=1000, le=3000, description="Année de mariage minimum")
    marriage_year_to: Optional[int] = Field(None, ge=1000, le=3000, description="Année de mariage maximum")
    divorce_year_from: Optional[int] = Field(None, ge=1000, le=3000, description="Année de divorce minimum")
    divorce_year_to: Optional[int] = Field(None, ge=1000, le=3000, description="Année de divorce maximum")
    place: Optional[str] = Field(None, description="Filtrer par lieu")
    has_children: Optional[bool] = Field(None, description="Filtrer par présence d'enfants")
    min_children: Optional[int] = Field(None, ge=0, description="Nombre minimum d'enfants")
    max_children: Optional[int] = Field(None, ge=0, description="Nombre maximum d'enfants")
    page: int = Field(1, ge=1, description="Numéro de page")
    size: int = Field(20, ge=1, le=100, description="Taille de la page")


class FamilyStatsSchema(BaseModel):
    """Schéma pour les statistiques des familles."""
    
    total: int = Field(..., ge=0, description="Nombre total de familles")
    by_status: Dict[str, int] = Field(..., description="Répartition par statut de mariage")
    by_century: Dict[str, int] = Field(..., description="Répartition par siècle de mariage")
    with_marriage_date: int = Field(..., ge=0, description="Nombre avec date de mariage")
    with_divorce_date: int = Field(..., ge=0, description="Nombre avec date de divorce")
    average_children: float = Field(..., ge=0, description="Nombre moyen d'enfants par famille")
    families_with_children: int = Field(..., ge=0, description="Nombre de familles avec enfants")
