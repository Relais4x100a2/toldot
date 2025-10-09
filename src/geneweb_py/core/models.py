"""
Modèles de données principaux pour geneweb-py

Ce module expose tous les modèles de données utilisés dans la librairie.
"""

from .date import CalendarType, Date, DatePrefix, DeathType
from .event import Event, EventType, FamilyEvent, FamilyEventType, PersonalEvent
from .family import Child, ChildSex, Family, MarriageStatus
from .genealogy import Genealogy, GenealogyMetadata
from .person import AccessLevel, Gender, Person, Title

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
