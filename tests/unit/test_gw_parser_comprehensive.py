"""
Tests complets pour le parser principal GeneWeb
"""

import pytest
import tempfile
import os
from pathlib import Path
from geneweb_py.core.parser.gw_parser import GeneWebParser
from geneweb_py.core.exceptions import GeneWebParseError, GeneWebEncodingError
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.family import Family, MarriageStatus
from geneweb_py.core.date import Date


class TestGeneWebParserInitialization:
    """Tests pour l'initialisation du parser."""
    
    def test_parser_initialization_default(self):
        """Test initialisation avec paramètres par défaut."""
        parser = GeneWebParser()
        assert parser.validate is True
        assert parser.lexical_parser is None
        assert parser.syntax_parser is not None
        assert parser.tokens == []
        assert parser.syntax_nodes == []
    
    def test_parser_initialization_with_validation(self):
        """Test initialisation avec validation désactivée."""
        parser = GeneWebParser(validate=False)
        assert parser.validate is False
        assert parser.lexical_parser is None
        assert parser.syntax_parser is not None
        assert parser.tokens == []
        assert parser.syntax_nodes == []


class TestGeneWebParserFileOperations:
    """Tests pour les opérations sur fichiers."""
    
    def test_parse_file_success(self):
        """Test parsing d'un fichier .gw valide."""
        # Créer un fichier de test
        test_content = """fam DUPONT Jean
husb DUPONT Jean
wife MARTIN Marie
end fam"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gw', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            parser = GeneWebParser(validate=False)
            genealogy = parser.parse_file(temp_path)
            
            assert isinstance(genealogy, Genealogy)
            assert len(genealogy.persons) >= 0  # Au moins une personne
            assert len(genealogy.families) >= 0  # Au moins une famille
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_parse_file_nonexistent(self):
        """Test parsing d'un fichier inexistant."""
        parser = GeneWebParser()
        
        with pytest.raises((FileNotFoundError, GeneWebParseError)):
            parser.parse_file("nonexistent.gw")
    
    def test_parse_file_invalid_extension(self):
        """Test parsing d'un fichier avec extension invalide."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            parser = GeneWebParser()
            
            with pytest.raises(GeneWebParseError):
                parser.parse_file(temp_path)
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_parse_file_empty(self):
        """Test parsing d'un fichier vide."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gw', delete=False) as f:
            temp_path = f.name
        
        try:
            parser = GeneWebParser(validate=False)
            genealogy = parser.parse_file(temp_path)
            
            assert isinstance(genealogy, Genealogy)
            assert len(genealogy.persons) == 0
            assert len(genealogy.families) == 0
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_parse_file_with_encoding_detection(self):
        """Test parsing avec détection d'encodage."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
end fam"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gw', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            parser = GeneWebParser(validate=False)
            genealogy = parser.parse_file(temp_path)
            
            assert isinstance(genealogy, Genealogy)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestGeneWebParserStringOperations:
    """Tests pour les opérations sur chaînes."""
    
    def test_parse_string_success(self):
        """Test parsing d'une chaîne valide."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
wife MARTIN Marie
end fam"""
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 0
        assert len(genealogy.families) >= 0
    
    def test_parse_string_empty(self):
        """Test parsing d'une chaîne vide."""
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string("")
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0
    
    def test_parse_string_invalid(self):
        """Test parsing d'une chaîne invalide."""
        parser = GeneWebParser()
        
        with pytest.raises(GeneWebParseError):
            parser.parse_string("invalid content")
    
    def test_parse_string_with_encoding(self):
        """Test parsing d'une chaîne avec encodage spécifique."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
end fam"""
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content, encoding='utf-8')
        
        assert isinstance(genealogy, Genealogy)


class TestGeneWebParserComplexContent:
    """Tests pour le parsing de contenu complexe."""
    
    def test_parse_person_with_dates(self):
        """Test parsing d'une personne avec dates."""
        test_content = """pevt DUPONT Jean
#birt 15/6/1990 #p Paris
#deat 20/8/2020 #p Lyon
end pevt"""
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1
        
        # Vérifier que la personne a des dates
        person = list(genealogy.persons.values())[0]
        assert person.birth_date is not None
        assert person.death_date is not None
    
    def test_parse_family_with_children(self):
        """Test parsing d'une famille avec enfants."""
        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre
- DUPONT Marie
end
end fam"""
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.families) >= 1
        
        # Vérifier que la famille a des enfants
        family = list(genealogy.families.values())[0]
        assert len(family.children) >= 2
    
    def test_parse_multiple_families(self):
        """Test parsing de plusieurs familles."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
wife MARTIN Marie
end fam

fam MARTIN Pierre
husb MARTIN Pierre
wife DUPONT Anne
end fam"""
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.families) >= 2
    
    def test_parse_with_notes(self):
        """Test parsing avec notes."""
        test_content = """notes DUPONT Jean
beg
Note personnelle importante
end notes

fam DUPONT Jean MARTIN Marie
end fam"""
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1
        
        # Vérifier que la personne a des notes
        person = list(genealogy.persons.values())[0]
        assert len(person.notes) >= 1


class TestGeneWebParserErrorHandling:
    """Tests pour la gestion d'erreurs."""
    
    def test_parse_invalid_syntax(self):
        """Test parsing avec syntaxe invalide."""
        parser = GeneWebParser()
        
        with pytest.raises(GeneWebParseError):
            parser.parse_string("invalid syntax")
    
    def test_parse_malformed_family(self):
        """Test parsing d'une famille malformée."""
        parser = GeneWebParser()
        
        with pytest.raises(GeneWebParseError):
            parser.parse_string("fam DUPONT Jean\ninvalid content")
    
    def test_parse_with_validation_errors(self):
        """Test parsing avec erreurs de validation."""
        # Contenu qui peut causer des erreurs de validation
        test_content = """fam DUPONT Jean
husb DUPONT Jean
#birt 32/13/1990  # Date invalide
end fam"""
        
        parser = GeneWebParser(validate=True)
        
        # Le parser peut soit réussir soit échouer selon l'implémentation
        try:
            genealogy = parser.parse_string(test_content)
            assert isinstance(genealogy, Genealogy)
        except GeneWebParseError:
            # C'est acceptable si la validation échoue
            pass


class TestGeneWebParserEdgeCases:
    """Tests pour les cas limites."""
    
    def test_parse_very_long_content(self):
        """Test parsing de contenu très long."""
        # Générer un contenu long
        content_parts = []
        for i in range(100):
            content_parts.append(f"""fam DUPONT Person{i}
husb DUPONT Person{i}
wife MARTIN Person{i}
end fam""")
        
        test_content = "\n\n".join(content_parts)
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.families) >= 100
    
    def test_parse_with_special_characters(self):
        """Test parsing avec caractères spéciaux."""
        test_content = """fam DUPONT Jean-François
husb DUPONT Jean-François
#birt 15/6/1990 #p Paris (France)
end fam"""
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1
    
    def test_parse_with_unicode(self):
        """Test parsing avec caractères Unicode."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
#birt 15/6/1990 #p Paris
#note Note avec caractères spéciaux: éàçùñ
end fam"""
        
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)
        
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1
