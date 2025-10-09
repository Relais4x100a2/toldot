"""
geneweb-py : Librairie Python pour le format GeneWeb (.gw)

Cette librairie permet de parser, manipuler et convertir les fichiers
généalogiques au format GeneWeb (.gw).
"""

__version__ = "0.1.0"
__author__ = "Guillaume Cayeux"
__email__ = "guillaume.cayeux@relais4x100a2.fr"

from .core.models import Date, Event, Family, Genealogy, Person
from .core.parser import GeneWebParser

__all__ = [
    "Person",
    "Family",
    "Event",
    "Date",
    "Genealogy",
    "GeneWebParser",
]
