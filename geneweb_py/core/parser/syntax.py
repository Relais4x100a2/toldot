"""
Parser syntaxique pour les fichiers .gw

Ce module implémente l'analyse syntaxique des tokens pour construire
l'arbre syntaxique des blocs structurés GeneWeb.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Iterator
from enum import Enum

from .lexical import Token, TokenType, LexicalParser
from ..exceptions import GeneWebParseError


class BlockType(Enum):
    """Types de blocs dans le format .gw"""
    FAMILY = "family"
    NOTES = "notes"
    RELATIONS = "relations"
    PERSON_EVENTS = "person_events"
    FAMILY_EVENTS = "family_events"
    DATABASE_NOTES = "database_notes"
    EXTENDED_PAGE = "extended_page"
    WIZARD_NOTE = "wizard_note"


@dataclass
class SyntaxNode:
    """Nœud de l'arbre syntaxique"""
    
    type: BlockType
    tokens: List[Token] = field(default_factory=list)
    children: List['SyntaxNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child: 'SyntaxNode') -> None:
        """Ajoute un enfant au nœud"""
        self.children.append(child)
    
    def add_token(self, token: Token) -> None:
        """Ajoute un token au nœud"""
        self.tokens.append(token)


class BlockParser:
    """Parser pour un type de bloc spécifique"""
    
    def __init__(self, block_type: BlockType):
        self.block_type = block_type
    
    def parse(self, tokens: List[Token], start_index: int) -> tuple[SyntaxNode, int]:
        """Parse un bloc et retourne le nœud et l'index suivant
        
        Args:
            tokens: Liste des tokens
            start_index: Index de début du bloc
            
        Returns:
            Tuple (nœud parsé, index suivant)
            
        Raises:
            GeneWebParseError: En cas d'erreur de parsing
        """
        raise NotImplementedError("Subclasses must implement parse method")


class FamilyBlockParser(BlockParser):
    """Parser spécialisé pour les blocs famille (fam)"""
    
    def __init__(self):
        super().__init__(BlockType.FAMILY)
    
    def parse(self, tokens: List[Token], start_index: int) -> tuple[SyntaxNode, int]:
        """Parse un bloc famille
        
        Format: fam HusbandName FirstName [+ WeddingDate] [#mp WeddingPlace] WifeName FirstName
        """
        node = SyntaxNode(BlockType.FAMILY)
        i = start_index
        
        # Vérifier que c'est bien un bloc fam
        if i >= len(tokens) or tokens[i].type != TokenType.FAM:
            raise GeneWebParseError(
                "Attendu 'fam' au début du bloc famille",
                tokens[i].line_number if i < len(tokens) else 0,
                token=tokens[i].value if i < len(tokens) else None,
                expected="fam"
            )
        
        node.add_token(tokens[i])
        i += 1
        
        # Parser les informations du mari
        i = self._parse_husband(tokens, i, node)
        
        # Parser le séparateur +
        if i < len(tokens) and tokens[i].type == TokenType.PLUS:
            node.add_token(tokens[i])
            i += 1
            
            # Parser la date de mariage (optionnelle)
            if i < len(tokens) and tokens[i].type == TokenType.DATE:
                node.add_token(tokens[i])
                i += 1
        
        # Parser les modificateurs de mariage
        i = self._parse_marriage_modifiers(tokens, i, node)
        
        # Parser les informations de la femme
        i = self._parse_wife(tokens, i, node)
        
        # Parser les témoins, sources, commentaires
        i = self._parse_additional_info(tokens, i, node)
        
        # Parser les enfants (bloc beg/end)
        i = self._parse_children(tokens, i, node)
        
        return node, i
    
    def _parse_husband(self, tokens: List[Token], start_index: int, node: SyntaxNode) -> int:
        """Parse les informations du mari"""
        i = start_index
        
        # Nom de famille
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            node.add_token(tokens[i])
            i += 1
        
        # Prénom
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            node.add_token(tokens[i])
            i += 1
        
        # Numéro d'occurrence (optionnel)
        if i < len(tokens) and tokens[i].type == TokenType.NUMBER:
            node.add_token(tokens[i])
            i += 1
        
        # Informations personnelles du mari (si pas déjà défini ailleurs)
        i = self._parse_personal_info(tokens, i, node)
        
        return i
    
    def _parse_wife(self, tokens: List[Token], start_index: int, node: SyntaxNode) -> int:
        """Parse les informations de la femme"""
        i = start_index
        
        # Nom de famille
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            node.add_token(tokens[i])
            i += 1
        
        # Prénom
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            node.add_token(tokens[i])
            i += 1
        
        # Numéro d'occurrence (optionnel)
        if i < len(tokens) and tokens[i].type == TokenType.NUMBER:
            node.add_token(tokens[i])
            i += 1
        
        # Informations personnelles de la femme (si pas déjà définie ailleurs)
        i = self._parse_personal_info(tokens, i, node)
        
        return i
    
    def _parse_personal_info(self, tokens: List[Token], start_index: int, node: SyntaxNode) -> int:
        """Parse les informations personnelles (dates, lieux, etc.)"""
        i = start_index
        
        # Date de naissance
        if i < len(tokens) and tokens[i].type == TokenType.DATE:
            node.add_token(tokens[i])
            i += 1
        
        # Lieu de naissance (#bp)
        if i < len(tokens) and tokens[i].type == TokenType.BP:
            node.add_token(tokens[i])
            i += 1
            if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                node.add_token(tokens[i])
                i += 1
        
        # Date de décès
        if i < len(tokens) and tokens[i].type == TokenType.DATE:
            node.add_token(tokens[i])
            i += 1
        
        # Lieu de décès (#dp)
        if i < len(tokens) and tokens[i].type == TokenType.DP:
            node.add_token(tokens[i])
            i += 1
            if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                node.add_token(tokens[i])
                i += 1
        
        return i
    
    def _parse_marriage_modifiers(self, tokens: List[Token], start_index: int, node: SyntaxNode) -> int:
        """Parse les modificateurs de mariage (#mp, #nm, etc.)"""
        i = start_index
        
        while i < len(tokens):
            token = tokens[i]
            
            # Modificateurs de lieu de mariage
            if token.type in [TokenType.MP, TokenType.P]:
                node.add_token(token)
                i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    node.add_token(tokens[i])
                    i += 1
                continue
            
            # Modificateurs de statut
            if token.type in [TokenType.NM, TokenType.ENG, TokenType.SEP, TokenType.DIV]:
                node.add_token(token)
                i += 1
                continue
            
            # Autres modificateurs
            if token.type in [TokenType.SRC, TokenType.S]:
                node.add_token(token)
                i += 1
                if i < len(tokens) and tokens[i].type in [TokenType.IDENTIFIER, TokenType.STRING]:
                    node.add_token(tokens[i])
                    i += 1
                continue
            
            break
        
        return i
    
    def _parse_additional_info(self, tokens: List[Token], start_index: int, node: SyntaxNode) -> int:
        """Parse les témoins, sources et commentaires supplémentaires"""
        i = start_index
        
        while i < len(tokens):
            token = tokens[i]
            
            # Témoins (wit)
            if token.type == TokenType.WIT:
                i = self._parse_witnesses(tokens, i, node)
                continue
            
            # Sources (src)
            if token.type == TokenType.SRC:
                node.add_token(token)
                i += 1
                if i < len(tokens) and tokens[i].type in [TokenType.IDENTIFIER, TokenType.STRING]:
                    node.add_token(tokens[i])
                    i += 1
                continue
            
            # Commentaires (comm)
            if token.type == TokenType.COMM:
                node.add_token(token)
                i += 1
                if i < len(tokens) and tokens[i].type in [TokenType.IDENTIFIER, TokenType.STRING]:
                    node.add_token(tokens[i])
                    i += 1
                continue
            
            # Lieux et sources communs pour les enfants
            if token.type in [TokenType.CBP, TokenType.CSRC]:
                node.add_token(token)
                i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    node.add_token(tokens[i])
                    i += 1
                continue
            
            # Fin de ligne ou début de bloc enfants
            if token.type == TokenType.NEWLINE:
                node.add_token(token)
                i += 1
                continue
            
            if token.type == TokenType.BEG:
                break
            
            # Token inattendu, on s'arrête
            break
        
        return i
    
    def _parse_witnesses(self, tokens: List[Token], start_index: int, node: SyntaxNode) -> int:
        """Parse les témoins du mariage"""
        i = start_index
        
        # Token wit
        node.add_token(tokens[i])
        i += 1
        
        # Type de témoin (m ou f)
        if i < len(tokens) and tokens[i].type in [TokenType.H, TokenType.F]:
            node.add_token(tokens[i])
            i += 1
        
        # Deux points
        if i < len(tokens) and tokens[i].type == TokenType.COLON:
            node.add_token(tokens[i])
            i += 1
        
        # Nom du témoin
        while i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            node.add_token(tokens[i])
            i += 1
        
        return i
    
    def _parse_children(self, tokens: List[Token], start_index: int, node: SyntaxNode) -> int:
        """Parse le bloc des enfants (beg/end)"""
        i = start_index
        
        # Début du bloc enfants
        if i < len(tokens) and tokens[i].type == TokenType.BEG:
            node.add_token(tokens[i])
            i += 1
            
            # Parser chaque enfant
            while i < len(tokens) and tokens[i].type == TokenType.DASH:
                child_node = SyntaxNode(BlockType.FAMILY)  # Enfant
                child_node.add_token(tokens[i])  # Tire
                i += 1
                
                # Sexe de l'enfant (optionnel)
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER and tokens[i].value in ['h', 'f']:
                    child_node.add_token(tokens[i])
                    i += 1
                
                # Nom de famille (si différent du père)
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    child_node.add_token(tokens[i])
                    i += 1
                
                # Prénom de l'enfant
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    child_node.add_token(tokens[i])
                    i += 1
                
                node.add_child(child_node)
            
            # Fin du bloc enfants
            if i < len(tokens) and tokens[i].type == TokenType.END:
                node.add_token(tokens[i])
                i += 1
        
        return i


class NotesBlockParser(BlockParser):
    """Parser spécialisé pour les blocs notes"""
    
    def __init__(self):
        super().__init__(BlockType.NOTES)
    
    def parse(self, tokens: List[Token], start_index: int) -> tuple[SyntaxNode, int]:
        """Parse un bloc notes
        
        Format: notes LastName FirstName[.Number]
        beg
        Notes content here
        end notes
        """
        node = SyntaxNode(BlockType.NOTES)
        i = start_index
        
        # Vérifier que c'est bien un bloc notes
        if i >= len(tokens) or tokens[i].type != TokenType.NOTES:
            raise GeneWebParseError(
                "Attendu 'notes' au début du bloc notes",
                tokens[i].line_number if i < len(tokens) else 0,
                token=tokens[i].value if i < len(tokens) else None,
                expected="notes"
            )
        
        node.add_token(tokens[i])
        i += 1
        
        # Nom de famille
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            node.add_token(tokens[i])
            i += 1
        
        # Prénom
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            node.add_token(tokens[i])
            i += 1
        
        # Numéro d'occurrence (optionnel)
        if i < len(tokens) and tokens[i].type == TokenType.NUMBER:
            node.add_token(tokens[i])
            i += 1
        
        # Parser le contenu des notes
        i = self._parse_notes_content(tokens, i, node)
        
        return node, i
    
    def _parse_notes_content(self, tokens: List[Token], start_index: int, node: SyntaxNode) -> int:
        """Parse le contenu des notes entre beg et end notes"""
        i = start_index
        
        # Début du contenu
        if i < len(tokens) and tokens[i].type == TokenType.BEG:
            node.add_token(tokens[i])
            i += 1
        
        # Contenu des notes (jusqu'à end notes)
        while i < len(tokens):
            if tokens[i].type == TokenType.END_NOTES:
                node.add_token(tokens[i])
                i += 1
                break
            else:
                node.add_token(tokens[i])
                i += 1
        
        return i


class SyntaxParser:
    """Parser syntaxique principal pour les fichiers .gw"""
    
    def __init__(self):
        self.block_parsers = {
            TokenType.FAM: FamilyBlockParser(),
            TokenType.NOTES: NotesBlockParser(),
            # TODO: Ajouter les autres parsers de blocs
        }
    
    def parse(self, tokens: List[Token]) -> List[SyntaxNode]:
        """Parse la liste complète des tokens
        
        Args:
            tokens: Liste des tokens du parser lexical
            
        Returns:
            Liste des nœuds syntaxiques
            
        Raises:
            GeneWebParseError: En cas d'erreur de parsing
        """
        nodes = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Ignorer les commentaires et espaces
            if token.type in [TokenType.COMMENT, TokenType.WHITESPACE, TokenType.NEWLINE]:
                i += 1
                continue
            
            # Parser les blocs reconnus
            if token.type in self.block_parsers:
                parser = self.block_parsers[token.type]
                try:
                    node, next_index = parser.parse(tokens, i)
                    nodes.append(node)
                    i = next_index
                except GeneWebParseError as e:
                    raise GeneWebParseError(
                        f"Erreur dans le bloc {token.type.value}: {e.message}",
                        e.line_number,
                        token=token.value
                    )
            else:
                # Token non reconnu, on l'ignore ou on lève une erreur
                i += 1
        
        return nodes
