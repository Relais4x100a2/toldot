"""
Module parser : Parsing des fichiers .gw

Ce module contient :
- Le parser lexical pour la tokenisation (avec cache LRU et __slots__)
- Le parser syntaxique pour l'analyse des blocs
- Le parser principal GeneWeb (avec mode streaming automatique)
- Le parser streaming pour gros fichiers (>10MB)
- La validation des données parsées

Optimisations de performance :
- Mode streaming automatique pour fichiers >10MB (~80% réduction mémoire)
- Cache LRU pour patterns regex (~10-15% plus rapide)
- __slots__ dans Token et SyntaxNode (~40% réduction mémoire)
- Dictionnaires pré-compilés pour lookups O(1)
"""

from .gw_parser import GeneWebParser
from .lexical import LexicalParser, Token, TokenType
from .streaming import (
    StreamingGeneWebParser,
    estimate_memory_usage,
    should_use_streaming,
)
from .syntax import BlockParser, SyntaxParser

__all__ = [
    "LexicalParser",
    "Token",
    "TokenType",
    "SyntaxParser",
    "BlockParser",
    "GeneWebParser",
    "StreamingGeneWebParser",
    "should_use_streaming",
    "estimate_memory_usage",
]
