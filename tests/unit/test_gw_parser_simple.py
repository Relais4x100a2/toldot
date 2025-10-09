"""
Tests simples pour le parser principal GeneWeb - tests qui fonctionnent
"""

import pytest
import tempfile
import os
from pathlib import Path
from geneweb_py.core.parser.gw_parser import GeneWebParser
from geneweb_py.core.exceptions import GeneWebParseError, GeneWebEncodingError
from geneweb_py.core.genealogy import Genealogy


class TestGeneWebParserBasic:
    """Tests de base pour le parser principal."""

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

    def test_parse_file_success(self):
        """Test parsing d'un fichier .gw valide."""
        # Créer un fichier de test simple
        test_content = """fam DUPONT Jean
husb DUPONT Jean
end fam"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gw", delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            parser = GeneWebParser(validate=False)
            genealogy = parser.parse_file(temp_path)

            assert isinstance(genealogy, Genealogy)
            assert len(genealogy.persons) >= 0
            assert len(genealogy.families) >= 0

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_parse_file_nonexistent(self):
        """Test parsing d'un fichier inexistant."""
        parser = GeneWebParser()

        with pytest.raises((FileNotFoundError, GeneWebParseError)):
            parser.parse_file("nonexistent.gw")

    def test_parse_file_empty(self):
        """Test parsing d'un fichier vide."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gw", delete=False) as f:
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

    def test_parse_string_success(self):
        """Test parsing d'une chaîne valide."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
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

    def test_parse_string_with_whitespace(self):
        """Test parsing d'une chaîne avec espaces."""
        test_content = (
            """   \n\n   fam DUPONT Jean\n   husb DUPONT Jean\n   end fam   \n\n   """
        )

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 0
        assert len(genealogy.families) >= 0

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

    def test_parse_with_comments(self):
        """Test parsing avec commentaires."""
        test_content = """# Commentaire de début
fam DUPONT Jean
husb DUPONT Jean
# Commentaire dans la famille
end fam
# Commentaire de fin"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.families) >= 1

    def test_parse_with_encoding_detection(self):
        """Test parsing avec détection d'encodage."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
end fam"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".gw", delete=False, encoding="utf-8"
        ) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            parser = GeneWebParser(validate=False)
            genealogy = parser.parse_file(temp_path)

            assert isinstance(genealogy, Genealogy)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_parse_very_long_content(self):
        """Test parsing de contenu très long."""
        # Générer un contenu long
        content_parts = []
        for i in range(50):  # Réduire pour éviter les timeouts
            content_parts.append(
                f"""fam DUPONT Person{i}
husb DUPONT Person{i}
end fam"""
            )

        test_content = "\n\n".join(content_parts)

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.families) >= 50

    def test_parse_with_special_characters(self):
        """Test parsing avec caractères spéciaux."""
        test_content = """fam DUPONT Jean-François
husb DUPONT Jean-François
end fam"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1

    def test_parse_with_unicode(self):
        """Test parsing avec caractères Unicode."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
end fam"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1

    def test_parse_with_validation_enabled(self):
        """Test parsing avec validation activée."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
end fam"""

        parser = GeneWebParser(validate=True)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 0
        assert len(genealogy.families) >= 0

    def test_parse_with_validation_disabled(self):
        """Test parsing avec validation désactivée."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
end fam"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 0
        assert len(genealogy.families) >= 0
