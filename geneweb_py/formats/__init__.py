"""
Module de conversion de formats pour geneweb-py.

Ce module fournit des convertisseurs pour transformer les données généalogiques
entre différents formats :
- GEDCOM (export et import)
- JSON (export et import)
- XML (export et import)
- Autres formats généalogiques

Classes principales :
- GEDCOMExporter : Export vers format GEDCOM
- GEDCOMImporter : Import depuis format GEDCOM
- JSONExporter : Export vers format JSON
- JSONImporter : Import depuis format JSON
- XMLExporter : Export vers format XML
- XMLImporter : Import depuis format XML
"""

from .gedcom import GEDCOMExporter, GEDCOMImporter
from .json import JSONExporter, JSONImporter
from .xml import XMLExporter, XMLImporter
from .base import BaseExporter, BaseImporter, ConversionError

__all__ = [
    # Classes de base
    "BaseExporter",
    "BaseImporter", 
    "ConversionError",
    
    # GEDCOM
    "GEDCOMExporter",
    "GEDCOMImporter",
    
    # JSON
    "JSONExporter", 
    "JSONImporter",
    
    # XML
    "XMLExporter",
    "XMLImporter",
]
