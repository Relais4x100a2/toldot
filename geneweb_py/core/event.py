"""
Modèle Event pour les événements généalogiques

Ce module définit les événements personnels et familiaux dans le format GeneWeb,
avec support des événements gwplus.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum
from .date import Date

if TYPE_CHECKING:
    from .person import Person


class EventType(Enum):
    """Types d'événements personnels"""
    # Événements de base
    BIRTH = "birt"
    BAPTISM = "bapt"
    DEATH = "deat"
    BURIAL = "buri"
    CREMATION = "crem"
    
    # Événements religieux
    CONFIRMATION = "conf"
    FIRST_COMMUNION = "fcom"
    ORDINATION = "ordn"
    EXCOMMUNICATION = "exco"
    
    # Événements civils
    NATURALIZATION = "natu"
    OCCUPATION = "occu"
    RESIDENCE = "resi"
    EDUCATION = "educ"
    GRADUATION = "grad"
    MILITARY_SERVICE = "mser"
    
    # Événements familiaux
    MARRIAGE = "marr"
    DIVORCE = "div"
    SEPARATION = "sep"
    ENGAGEMENT = "enga"
    PACS = "pacs"


class FamilyEventType(Enum):
    """Types d'événements familiaux (gwplus)"""
    MARRIAGE = "marr"
    NO_MARRIAGE = "nmar"
    NO_MENTION = "nmen"
    ENGAGEMENT = "enga"
    DIVORCE = "div"
    SEPARATION = "sep"
    ANNULMENT = "anul"
    MARRIAGE_BANN = "marb"
    MARRIAGE_CONTRACT = "marc"
    MARRIAGE_LICENSE = "marl"
    PACS = "pacs"
    RESIDENCE = "resi"
    NAME_STRING = "strng"


@dataclass
class Event:
    """Représentation d'un événement généalogique
    
    Un événement peut être personnel (pevt) ou familial (fevt) selon le contexte.
    """
    
    # Type d'événement
    event_type: EventType
    
    # Date de l'événement
    date: Optional[Date] = None
    
    # Lieu de l'événement
    place: Optional[str] = None
    
    # Source de l'événement
    source: Optional[str] = None
    
    # Raison ou cause de l'événement
    reason: Optional[str] = None
    
    # Témoins (pour les événements familiaux)
    witnesses: List[Dict[str, Any]] = field(default_factory=list)
    
    # Notes sur l'événement
    notes: List[str] = field(default_factory=list)
    
    # Informations spécifiques selon le type d'événement
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_witness(self, person_id: str, witness_type: Optional[str] = None) -> None:
        """Ajoute un témoin à l'événement
        
        Args:
            person_id: ID de la personne témoin
            witness_type: Type de témoin (m=masculin, f=féminin, etc.)
        """
        witness_info = {
            'person_id': person_id,
            'type': witness_type
        }
        self.witnesses.append(witness_info)
    
    def add_note(self, note: str) -> None:
        """Ajoute une note à l'événement"""
        self.notes.append(note)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Définit une métadonnée spécifique à l'événement"""
        self.metadata[key] = value
    
    @property
    def display_name(self) -> str:
        """Retourne le nom d'affichage de l'événement"""
        return self.event_type.value.upper()
    
    @property
    def is_family_event(self) -> bool:
        """Vérifie si c'est un événement familial"""
        family_events = {
            EventType.MARRIAGE, EventType.DIVORCE, EventType.SEPARATION,
            EventType.ENGAGEMENT, EventType.PACS
        }
        return self.event_type in family_events
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'événement en dictionnaire pour sérialisation"""
        return {
            'type': self.event_type.value,
            'date': self.date.display_text if self.date else None,
            'place': self.place,
            'source': self.source,
            'witnesses': [w['person_id'] for w in self.witnesses],
            'notes': self.notes,
            'metadata': self.metadata
        }


@dataclass
class FamilyEvent(Event):
    """Événement familial spécifique (format gwplus)"""
    
    family_event_type: FamilyEventType = None
    
    def __post_init__(self):
        """Initialisation post-création"""
        if self.family_event_type:
            # Mapper le type familial vers le type générique
            mapping = {
                FamilyEventType.MARRIAGE: EventType.MARRIAGE,
                FamilyEventType.DIVORCE: EventType.DIVORCE,
                FamilyEventType.SEPARATION: EventType.SEPARATION,
                FamilyEventType.ENGAGEMENT: EventType.ENGAGEMENT,
                FamilyEventType.PACS: EventType.PACS,
            }
            if self.family_event_type in mapping:
                self.event_type = mapping[self.family_event_type]
    
    @property
    def is_family_event(self) -> bool:
        """Les événements familiaux sont toujours des événements familiaux"""
        return True


@dataclass
class PersonalEvent(Event):
    """Événement personnel spécifique (format gwplus)"""
    
    def __post_init__(self):
        """Initialisation post-création"""
        # Les événements personnels ne sont jamais familiaux
        pass
    
    @property
    def is_family_event(self) -> bool:
        """Les événements personnels ne sont jamais familiaux"""
        return False
