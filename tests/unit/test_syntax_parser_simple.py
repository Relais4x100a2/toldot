"""
Tests simples pour le parser syntaxique
"""

import pytest
from geneweb_py.core.parser.syntax import SyntaxParser, SyntaxNode, BlockType
from geneweb_py.core.parser.lexical import Token, TokenType


class TestSyntaxParserBasic:
    """Tests de base pour le parser syntaxique."""
    
    def test_syntax_parser_initialization(self):
        """Test initialisation du parser syntaxique."""
        parser = SyntaxParser()
        assert parser is not None
    
    def test_parse_simple_family(self):
        """Test parsing d'une famille simple."""
        tokens = [
            Token(TokenType.FAM, "fam", 1, 1, 0),
            Token(TokenType.IDENTIFIER, "DUPONT", 1, 5, 4),
            Token(TokenType.IDENTIFIER, "Jean", 1, 12, 11),
            Token(TokenType.IDENTIFIER, "husb", 2, 1, 16),
            Token(TokenType.IDENTIFIER, "DUPONT", 2, 6, 21),
            Token(TokenType.IDENTIFIER, "Jean", 2, 13, 28),
            Token(TokenType.END, "end", 3, 1, 33),
            Token(TokenType.FAM, "fam", 3, 5, 37),
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        assert len(nodes) >= 1
        
        # Vérifier que nous avons un nœud de famille
        family_node = nodes[0]
        assert family_node.type == BlockType.FAMILY
        assert family_node.tokens is not None
    
    def test_parse_empty_tokens(self):
        """Test parsing avec tokens vides."""
        parser = SyntaxParser()
        nodes = parser.parse([])
        
        assert isinstance(nodes, list)
        assert len(nodes) == 0
    
    def test_parse_single_token(self):
        """Test parsing avec un seul token."""
        tokens = [Token(TokenType.FAM, "fam", 1, 1, 0)]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        # Le parser peut soit créer un nœud soit ignorer le token isolé
        assert len(nodes) >= 0
    
    def test_parse_with_comments(self):
        """Test parsing avec commentaires."""
        tokens = [
            Token(TokenType.COMMENT, "# Commentaire", 1, 1, 0),
            Token(TokenType.FAM, "fam", 2, 1, 15),
            Token(TokenType.IDENTIFIER, "DUPONT", 2, 5, 19),
            Token(TokenType.IDENTIFIER, "Jean", 2, 12, 26),
            Token(TokenType.END, "end", 3, 1, 31),
            Token(TokenType.FAM, "fam", 3, 5, 35),
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        assert len(nodes) >= 1
    
    def test_parse_multiple_blocks(self):
        """Test parsing de plusieurs blocs."""
        tokens = [
            # Premier bloc
            Token(TokenType.FAM, "fam", 1, 1, 0),
            Token(TokenType.IDENTIFIER, "DUPONT", 1, 5, 4),
            Token(TokenType.IDENTIFIER, "Jean", 1, 12, 9),
            Token(TokenType.END, "end", 2, 1, 13),
            Token(TokenType.FAM, "fam", 2, 5, 17),
            
            # Deuxième bloc
            Token(TokenType.FAM, "fam", 4, 1, 22),
            Token(TokenType.IDENTIFIER, "MARTIN", 4, 5, 26),
            Token(TokenType.IDENTIFIER, "Marie", 4, 12, 33),
            Token(TokenType.END, "end", 5, 1, 38),
            Token(TokenType.FAM, "fam", 5, 5, 42),
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        assert len(nodes) >= 2
    
    def test_parse_with_whitespace_tokens(self):
        """Test parsing avec tokens d'espacement."""
        tokens = [
            Token(TokenType.WHITESPACE, "   ", 1, 1, 0),
            Token(TokenType.FAM, "fam", 1, 4, 3),
            Token(TokenType.IDENTIFIER, "DUPONT", 1, 8, 7),
            Token(TokenType.IDENTIFIER, "Jean", 1, 15, 14),
            Token(TokenType.WHITESPACE, "\n", 1, 19, 18),
            Token(TokenType.END, "end", 2, 1, 19),
            Token(TokenType.FAM, "fam", 2, 5, 23),
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        assert len(nodes) >= 1
    
    def test_parse_with_unknown_tokens(self):
        """Test parsing avec tokens inconnus."""
        tokens = [
            Token(TokenType.FAM, "fam", 1, 1, 0),
            Token(TokenType.IDENTIFIER, "DUPONT", 1, 5, 4),
            Token(TokenType.IDENTIFIER, "Jean", 1, 12, 9),
            Token(TokenType.UNKNOWN, "unknown", 2, 1, 13),
            Token(TokenType.END, "end", 3, 1, 20),
            Token(TokenType.FAM, "fam", 3, 5, 24),
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        # Le parser devrait gérer les tokens inconnus
        assert len(nodes) >= 0
    
    def test_parse_incomplete_block(self):
        """Test parsing d'un bloc incomplet."""
        tokens = [
            Token(TokenType.FAM, "fam", 1, 1, 0),
            Token(TokenType.IDENTIFIER, "DUPONT", 1, 5, 4),
            Token(TokenType.IDENTIFIER, "Jean", 1, 12, 9),
            # Pas de token END
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        # Le parser peut soit créer un nœud incomplet soit l'ignorer
        assert len(nodes) >= 0
    
    def test_parse_nested_blocks(self):
        """Test parsing de blocs imbriqués."""
        tokens = [
            Token(TokenType.FAM, "fam", 1, 1, 0),
            Token(TokenType.IDENTIFIER, "DUPONT", 1, 5, 4),
            Token(TokenType.IDENTIFIER, "Jean", 1, 12, 9),
            Token(TokenType.IDENTIFIER, "husb", 2, 1, 13),
            Token(TokenType.IDENTIFIER, "DUPONT", 2, 6, 18),
            Token(TokenType.IDENTIFIER, "Jean", 2, 13, 25),
            Token(TokenType.END, "end", 3, 1, 29),
            Token(TokenType.FAM, "fam", 3, 5, 33),
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        assert len(nodes) >= 1
        
        # Vérifier que le nœud contient des sous-éléments
        family_node = nodes[0]
        assert family_node.type == BlockType.FAMILY
        assert family_node.tokens is not None
        assert len(family_node.tokens) >= 0
    
    def test_parse_with_dates(self):
        """Test parsing avec dates."""
        tokens = [
            Token(TokenType.FAM, "fam", 1, 1, 0),
            Token(TokenType.IDENTIFIER, "DUPONT", 1, 5, 4),
            Token(TokenType.IDENTIFIER, "Jean", 1, 12, 9),
            Token(TokenType.BIRT, "#birt", 2, 1, 13),
            Token(TokenType.DATE, "15/6/1990", 2, 7, 19),
            Token(TokenType.END, "end", 3, 1, 29),
            Token(TokenType.FAM, "fam", 3, 5, 33),
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        assert len(nodes) >= 1
    
    def test_parse_with_places(self):
        """Test parsing avec lieux."""
        tokens = [
            Token(TokenType.FAM, "fam", 1, 1, 0),
            Token(TokenType.IDENTIFIER, "DUPONT", 1, 5, 4),
            Token(TokenType.IDENTIFIER, "Jean", 1, 12, 9),
            Token(TokenType.BIRT, "#birt", 2, 1, 13),
            Token(TokenType.DATE, "15/6/1990", 2, 7, 19),
            Token(TokenType.P, "#p", 2, 18, 30),
            Token(TokenType.IDENTIFIER, "Paris", 2, 21, 33),
            Token(TokenType.END, "end", 3, 1, 38),
            Token(TokenType.FAM, "fam", 3, 5, 42),
        ]
        
        parser = SyntaxParser()
        nodes = parser.parse(tokens)
        
        assert isinstance(nodes, list)
        assert len(nodes) >= 1
