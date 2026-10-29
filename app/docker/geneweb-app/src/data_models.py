"""
Modèles de données pour les événements PEVT
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Types d'événements standard GeneWeb"""
    BIRTH = "naissance"
    DEATH = "décès"
    MARRIAGE = "mariage"
    BAPTISM = "baptême"
    BURIAL = "inhumation"
    EDUCATION = "éducation"
    OCCUPATION = "profession"
    RESIDENCE = "résidence"
    CUSTOM = "personnalisé"


@dataclass
class PEVTRaw:
    """Événement PEVT brut extrait du fichier .gw"""
    person_name: str
    person_surname: str
    event_tag: str  # Ex: #Cours_peinture, #DUEJ, etc.
    date: Optional[str] = None
    place: Optional[str] = None
    raw_text: str = ""  # Le texte complet de l'événement
    witnesses: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class PEVTCleaned:
    """Événement PEVT nettoyé et structuré"""
    # Données originales
    original: PEVTRaw
    
    # Données nettoyées
    event_type: EventType
    date_iso: Optional[str] = None  # Format ISO YYYY-MM-DD
    date_uncertainty: Optional[str] = None  # "~", "before", "after", "between"
    place_structured: Dict[str, str] = field(default_factory=dict)  # ville, code_insee, département, etc.
    organization: Optional[str] = None
    description: str = ""
    
    # Métadonnées
    confidence_score: float = 0.0  # 0.0 à 1.0
    needs_review: bool = False
    transformation_notes: List[str] = field(default_factory=list)
    cleaned_by: str = "manual"  # "manual", "llm", "dspy"
    cleaned_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AnnotationExample:
    """Exemple d'annotation pour l'entraînement"""
    pevt_raw: PEVTRaw
    pevt_cleaned: PEVTCleaned
    annotator: str
    annotation_time: float = 0.0  # Temps passé en secondes
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PromptVersion:
    """Version du prompt pour le tracking"""
    version: int
    prompt_text: str
    examples_count: int
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class ValidationResult:
    """Résultat de validation d'une transformation"""
    pevt_cleaned: PEVTCleaned
    is_correct: bool
    errors: List[str] = field(default_factory=list)
    corrections: Dict[str, Any] = field(default_factory=dict)
    validator: str = ""
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())
