"""
Tests pour améliorer la couverture du parser syntaxique
"""

import pytest
from geneweb_py.core.parser.syntax import (
    SyntaxParser, SyntaxNode, BlockType, FamilyBlockParser, 
    NotesBlockParser, PersonEventsBlockParser,
    FamilyEventsBlockParser, BlockParser
)
from geneweb_py.core.parser.lexical import Token, TokenType, LexicalParser
from geneweb_py.core.exceptions import GeneWebParseError


def create_token(token_type: TokenType, value: str, line: int = 1, column: int = 1, position: int = 0) -> Token:
    """Helper pour créer des tokens facilement"""
    return Token(token_type, value, line, column, position)


class TestBlockParserCoverage:
    """Tests pour la classe BlockParser abstraite"""
    
    def test_block_parser_abstract_method(self):
        """Test que la méthode parse est abstraite"""
        parser = BlockParser(BlockType.FAMILY)
        tokens = [create_token(TokenType.FAM, "fam")]
        
        with pytest.raises(NotImplementedError):
            parser.parse(tokens, 0)


class TestSyntaxParserCoverage:
    """Tests pour améliorer la couverture du parser syntaxique"""
    
    def test_syntax_parser_initialization(self):
        """Test initialisation du parser syntaxique"""
        parser = SyntaxParser()
        assert parser is not None
        assert parser.block_parsers is not None
    
    def test_syntax_node_creation(self):
        """Test création d'un nœud syntaxique"""
        node = SyntaxNode(BlockType.FAMILY)
        assert node.type == BlockType.FAMILY
        assert node.tokens == []
        assert node.children == []
        assert node.metadata == {}
    
    def test_syntax_node_add_token(self):
        """Test ajout de token à un nœud"""
        node = SyntaxNode(BlockType.FAMILY)
        token = create_token(TokenType.FAM, "fam")
        node.add_token(token)
        assert len(node.tokens) == 1
        assert node.tokens[0] == token
    
    def test_syntax_node_add_child(self):
        """Test ajout d'enfant à un nœud"""
        parent = SyntaxNode(BlockType.FAMILY)
        child = SyntaxNode(BlockType.NOTES)
        parent.add_child(child)
        assert len(parent.children) == 1
        assert parent.children[0] == child
    
    def test_syntax_node_set_metadata(self):
        """Test définition de métadonnées"""
        node = SyntaxNode(BlockType.FAMILY)
        node.metadata["test_key"] = "test_value"
        assert node.metadata["test_key"] == "test_value"


class TestFamilyBlockParserCoverage:
    """Tests pour améliorer la couverture du parser de blocs famille"""
    
    def test_family_block_parser_initialization(self):
        """Test initialisation du parser de blocs famille"""
        parser = FamilyBlockParser()
        assert parser.block_type == BlockType.FAMILY
    
    def test_family_block_parser_invalid_start(self):
        """Test parsing avec token de début invalide"""
        parser = FamilyBlockParser()
        tokens = [create_token(TokenType.IDENTIFIER, "invalid")]
        
        with pytest.raises(GeneWebParseError) as exc_info:
            parser.parse(tokens, 0)
        
        assert "Attendu 'fam'" in str(exc_info.value)
        assert exc_info.value.line_number == 1
        assert exc_info.value.token == "invalid"
    
    def test_family_block_parser_empty_tokens(self):
        """Test parsing avec liste de tokens vide"""
        parser = FamilyBlockParser()
        tokens = []
        
        with pytest.raises(GeneWebParseError) as exc_info:
            parser.parse(tokens, 0)
        
        assert "Attendu 'fam'" in str(exc_info.value)
        assert exc_info.value.line_number == 0


class TestNotesBlockParserCoverage:
    """Tests pour améliorer la couverture du parser de blocs notes"""
    
    def test_notes_block_parser_initialization(self):
        """Test initialisation du parser de blocs notes"""
        parser = NotesBlockParser()
        assert parser.block_type == BlockType.NOTES
    
    def test_notes_block_parser_invalid_start(self):
        """Test parsing avec token de début invalide"""
        parser = NotesBlockParser()
        tokens = [create_token(TokenType.IDENTIFIER, "invalid")]
        
        with pytest.raises(GeneWebParseError) as exc_info:
            parser.parse(tokens, 0)
        
        assert "Attendu 'notes'" in str(exc_info.value)
    
    def test_notes_block_parser_empty_tokens(self):
        """Test parsing avec liste de tokens vide"""
        parser = NotesBlockParser()
        tokens = []
        
        with pytest.raises(GeneWebParseError) as exc_info:
            parser.parse(tokens, 0)
        
        assert "Attendu 'notes'" in str(exc_info.value)


class TestPersonEventsBlockParserCoverage:
    """Tests pour améliorer la couverture du parser de blocs événements personnels"""
    
    def test_person_events_block_parser_initialization(self):
        """Test initialisation du parser de blocs événements personnels"""
        parser = PersonEventsBlockParser()
        assert parser.block_type == BlockType.PERSON_EVENTS
    
    def test_person_events_block_parser_invalid_start(self):
        """Test parsing avec token de début invalide"""
        parser = PersonEventsBlockParser()
        tokens = [create_token(TokenType.IDENTIFIER, "invalid")]
        
        with pytest.raises(GeneWebParseError) as exc_info:
            parser.parse(tokens, 0)
        
        assert "Attendu 'pevt'" in str(exc_info.value)


class TestFamilyEventsBlockParserCoverage:
    """Tests pour améliorer la couverture du parser de blocs événements familiaux"""
    
    def test_family_events_block_parser_initialization(self):
        """Test initialisation du parser de blocs événements familiaux"""
        parser = FamilyEventsBlockParser()
        assert parser.block_type == BlockType.FAMILY_EVENTS
    
    def test_family_events_block_parser_invalid_start(self):
        """Test parsing avec token de début invalide"""
        parser = FamilyEventsBlockParser()
        tokens = [create_token(TokenType.IDENTIFIER, "invalid")]
        
        with pytest.raises(GeneWebParseError) as exc_info:
            parser.parse(tokens, 0)
        
        assert "Attendu 'fevt'" in str(exc_info.value)


class TestSyntaxParserIntegrationCoverage:
    """Tests d'intégration pour améliorer la couverture"""
    
    def test_syntax_parser_parse_empty_tokens(self):
        """Test parsing avec tokens vides"""
        parser = SyntaxParser()
        tokens = []
        
        nodes = parser.parse(tokens)
        assert len(nodes) == 0
    
    def test_syntax_parser_parse_with_whitespace_only(self):
        """Test parsing avec seulement des espaces"""
        parser = SyntaxParser()
        tokens = [
            create_token(TokenType.WHITESPACE, " "),
            create_token(TokenType.NEWLINE, "\n"),
            create_token(TokenType.WHITESPACE, "  ", line=2),
        ]
        
        nodes = parser.parse(tokens)
        assert len(nodes) == 0
    
    def test_syntax_parser_parse_with_unknown_block(self):
        """Test parsing avec bloc inconnu"""
        parser = SyntaxParser()
        tokens = [
            create_token(TokenType.IDENTIFIER, "unknown"),
            create_token(TokenType.IDENTIFIER, "block"),
        ]
        
        # Le parser devrait ignorer les blocs inconnus
        nodes = parser.parse(tokens)
        assert len(nodes) == 0