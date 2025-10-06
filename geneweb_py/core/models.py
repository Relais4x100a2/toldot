"""
Modèles de données principaux pour geneweb-py

Ce module expose tous les modèles de données utilisés dans la librairie.
"""

from .person import Person, Title, Gender, AccessLevel
from .family import Family, Child, MarriageStatus, ChildSex
from .event import Event, FamilyEvent, PersonalEvent, EventType, FamilyEventType
from .date import Date, DatePrefix, CalendarType, DeathType
from .genealogy import Genealogy, GenealogyMetadata

__all__ = [
    # Personnes
    "Person",
    "Title", 
    "Gender",
    "AccessLevel",
    
    # Familles
    "Family",
    "Child",
    "MarriageStatus",
    "ChildSex",
    
    # Événements
    "Event",
    "FamilyEvent", 
    "PersonalEvent",
    "EventType",
    "FamilyEventType",
    
    # Dates
    "Date",
    "DatePrefix",
    "CalendarType", 
    "DeathType",
    
    # Généalogie
    "Genealogy",
    "GenealogyMetadata",
]
