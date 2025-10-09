"""
geneweb-py : Librairie Python pour le format GeneWeb (.gw)

Cette librairie permet de parser, manipuler et convertir les fichiers
généalogiques au format GeneWeb (.gw).
"""

__version__ = "0.1.0"
__author__ = "Guillaume Cayeux"
__email__ = "guillaume@example.com"

from .core.models import Person, Family, Event, Date, Genealogy
from .core.parser import GeneWebParser

__all__ = [
    "Person",
    "Family",
    "Event",
    "Date",
    "Genealogy",
    "GeneWebParser",
]
