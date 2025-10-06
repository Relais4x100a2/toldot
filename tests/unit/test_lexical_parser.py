"""
Tests unitaires pour le parser lexical

Ces tests vérifient la tokenisation correcte des fichiers .gw
avec tous les types de tokens supportés.
"""

import pytest
from geneweb_py.core.parser.lexical import LexicalParser, Token, TokenType
from geneweb_py.core.exceptions import GeneWebParseError


class TestLexicalParser:
    """Tests pour le parser lexical"""
    
    def test_simple_family_block(self):
        """Test tokenisation d'un bloc famille simple"""
        content = "fam CORNO Joseph + THOMAS Marie"
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier les tokens attendus
        expected_types = [
            TokenType.FAM,
            TokenType.IDENTIFIER,  # CORNO
            TokenType.IDENTIFIER,  # Joseph
            TokenType.PLUS,
            TokenType.IDENTIFIER,  # THOMAS
            TokenType.IDENTIFIER,  # Marie
            TokenType.EOF
        ]
        
        assert len(tokens) == len(expected_types)
        for i, expected_type in enumerate(expected_types):
            assert tokens[i].type == expected_type
    
    def test_family_with_marriage_date(self):
        """Test tokenisation avec date de mariage"""
        content = "fam CORNO Joseph + 10/08/2015 THOMAS Marie"
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier la présence du token DATE
        date_token = next((t for t in tokens if t.type == TokenType.DATE), None)
        assert date_token is not None
        assert date_token.value == "10/08/2015"
    
    def test_hash_modifiers(self):
        """Test tokenisation des modificateurs avec #"""
        content = "fam CORNO Joseph #bp Paris + THOMAS Marie"
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier les modificateurs
        bp_token = next((t for t in tokens if t.type == TokenType.BP), None)
        assert bp_token is not None
        assert bp_token.value == "#bp"
    
    def test_complex_date_formats(self):
        """Test tokenisation des dates complexes"""
        test_cases = [
            ("25/12/1990", "25/12/1990"),
            ("~10/5/1990", "~10/5/1990"),
            ("?15/06/1992", "?15/06/1992"),
            ("<01/01/2020", "<01/01/2020"),
            (">31/12/2019", ">31/12/2019"),
            ("10/9/5750H", "10/9/5750H"),
            ("0(5_Mai_1990)", "0(5_Mai_1990)"),
            ("0", "0")
        ]
        
        for date_str, expected_value in test_cases:
            content = f"fam CORNO Joseph {date_str} THOMAS Marie"
            parser = LexicalParser(content)
            tokens = parser.tokenize()
            
            date_token = next((t for t in tokens if t.type == TokenType.DATE), None)
            assert date_token is not None, f"Date token not found for: {date_str}"
            assert date_token.value == expected_value
    
    def test_notes_block(self):
        """Test tokenisation d'un bloc notes"""
        content = """notes CORNO Joseph
beg
Notes personnelles de Joseph CORNO.
end notes"""
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier les tokens attendus
        expected_types = [
            TokenType.NOTES,
            TokenType.IDENTIFIER,  # CORNO
            TokenType.IDENTIFIER,  # Joseph
            TokenType.NEWLINE,
            TokenType.BEG,
            TokenType.NEWLINE,
            TokenType.IDENTIFIER,  # Notes
            TokenType.IDENTIFIER,  # personnelles
            TokenType.DOT,
            TokenType.IDENTIFIER,  # de
            TokenType.IDENTIFIER,  # Joseph
            TokenType.IDENTIFIER,  # CORNO
            TokenType.DOT,
            TokenType.NEWLINE,
            TokenType.END_NOTES,
            TokenType.EOF
        ]
        
        # Filtrer les tokens pertinents (ignorer les espaces)
        relevant_tokens = [t for t in tokens if t.type != TokenType.WHITESPACE]
        assert len(relevant_tokens) == len(expected_types)
        
        for i, expected_type in enumerate(expected_types):
            assert relevant_tokens[i].type == expected_type
    
    def test_comments(self):
        """Test tokenisation des commentaires"""
        content = """# Commentaire sur une ligne
fam CORNO Joseph + THOMAS Marie"""
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier la présence du commentaire
        comment_token = next((t for t in tokens if t.type == TokenType.COMMENT), None)
        assert comment_token is not None
        assert comment_token.value == "# Commentaire sur une ligne"
    
    def test_witnesses(self):
        """Test tokenisation des témoins"""
        content = """fam CORNO Joseph + THOMAS Marie
wit m: DUPONT Pierre
wit f: MARTIN Claire"""
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier les témoins
        wit_tokens = [t for t in tokens if t.type == TokenType.WIT]
        assert len(wit_tokens) == 2
        
        # Vérifier les types de témoins
        h_tokens = [t for t in tokens if t.type == TokenType.H]
        f_tokens = [t for t in tokens if t.type == TokenType.F]
        assert len(h_tokens) == 1  # m (masculin)
        assert len(f_tokens) == 1  # f (féminin)
    
    def test_children_block(self):
        """Test tokenisation du bloc enfants"""
        content = """fam CORNO Joseph + THOMAS Marie
beg
- h CORNO Jean
- f CORNO Sophie
end"""
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier les tokens attendus
        beg_token = next((t for t in tokens if t.type == TokenType.BEG), None)
        end_token = next((t for t in tokens if t.type == TokenType.END), None)
        
        assert beg_token is not None
        assert end_token is not None
        
        # Vérifier les tirets des enfants
        dash_tokens = [t for t in tokens if t.type == TokenType.DASH]
        assert len(dash_tokens) == 2
    
    def test_string_literals(self):
        """Test tokenisation des chaînes littérales"""
        content = 'fam CORNO Joseph + THOMAS Marie\nsrc "Acte de mariage, mairie de Paris"'
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier la chaîne
        string_token = next((t for t in tokens if t.type == TokenType.STRING), None)
        assert string_token is not None
        assert string_token.value == "Acte de mariage, mairie de Paris"
    
    def test_occurrence_numbers(self):
        """Test tokenisation des numéros d'occurrence"""
        content = "fam CORNO Joseph.1 + THOMAS Marie.2"
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier les numéros
        number_tokens = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(number_tokens) == 2
        assert number_tokens[0].value == ".1"
        assert number_tokens[1].value == ".2"
    
    def test_line_numbers_and_positions(self):
        """Test que les numéros de ligne et positions sont corrects"""
        content = """fam CORNO Joseph
+ THOMAS Marie
beg
- CORNO Jean
end"""
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier les numéros de ligne
        fam_token = next((t for t in tokens if t.type == TokenType.FAM), None)
        assert fam_token.line_number == 1
        
        plus_token = next((t for t in tokens if t.type == TokenType.PLUS), None)
        assert plus_token.line_number == 2
        
        beg_token = next((t for t in tokens if t.type == TokenType.BEG), None)
        assert beg_token.line_number == 3
    
    def test_empty_content(self):
        """Test avec contenu vide"""
        parser = LexicalParser("")
        tokens = parser.tokenize()
        
        # Doit contenir seulement le token EOF
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF
    
    def test_whitespace_only(self):
        """Test avec seulement des espaces"""
        parser = LexicalParser("   \n  \t  ")
        tokens = parser.tokenize()
        
        # Doit contenir seulement le token EOF
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF
    
    def test_unknown_tokens(self):
        """Test avec des tokens inconnus"""
        content = "fam CORNO Joseph @ THOMAS Marie"
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        
        # Vérifier la présence du token inconnu
        unknown_token = next((t for t in tokens if t.type == TokenType.UNKNOWN), None)
        assert unknown_token is not None
        assert unknown_token.value == "@"


class TestToken:
    """Tests pour la classe Token"""
    
    def test_token_creation(self):
        """Test création d'un token"""
        token = Token(
            type=TokenType.FAM,
            value="fam",
            line_number=1,
            column=1,
            position=0
        )
        
        assert token.type == TokenType.FAM
        assert token.value == "fam"
        assert token.line_number == 1
        assert token.column == 1
        assert token.position == 0
    
    def test_token_string_representation(self):
        """Test représentation string du token"""
        token = Token(
            type=TokenType.IDENTIFIER,
            value="CORNO",
            line_number=5,
            column=10,
            position=100
        )
        
        expected = "identifier('CORNO')@5:10"
        assert str(token) == expected
    
    def test_token_repr(self):
        """Test représentation pour debug"""
        token = Token(
            type=TokenType.DATE,
            value="25/12/1990",
            line_number=2,
            column=5,
            position=20
        )
        
        expected = "Token(date, '25/12/1990', 2:5)"
        assert repr(token) == expected
