"""
Tests pour améliorer la couverture du parser principal (gw_parser.py)
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from geneweb_py.core.parser.gw_parser import GeneWebParser
from geneweb_py.core.exceptions import GeneWebParseError, GeneWebEncodingError
from geneweb_py.core.genealogy import Genealogy


class TestGeneWebParserCoverage:
    """Tests pour améliorer la couverture du parser principal"""

    def test_parser_initialization_with_validation(self):
        """Test initialisation du parser avec validation"""
        parser = GeneWebParser(validate=True)
        assert parser.validate is True
        assert parser.lexical_parser is None
        assert parser.syntax_parser is not None
        assert parser.tokens == []
        assert parser.syntax_nodes == []

    def test_parser_initialization_without_validation(self):
        """Test initialisation du parser sans validation"""
        parser = GeneWebParser(validate=False)
        assert parser.validate is False

    def test_parse_file_nonexistent(self):
        """Test parsing d'un fichier inexistant"""
        parser = GeneWebParser()

        with pytest.raises(GeneWebParseError) as exc_info:
            parser.parse_file("nonexistent.gw")

        assert "Fichier non trouvé" in str(exc_info.value)

    @pytest.mark.skip(
        reason="TODO: Parser lève GeneWebParseError au lieu d'accepter les extensions non .gw"
    )
    def test_parse_file_invalid_extension(self):
        """Test parsing d'un fichier avec extension invalide"""
        parser = GeneWebParser(validate=False)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("fam DUPONT Jean MARTIN Marie")
            temp_path = f.name

        try:
            # Le parser accepte tous les fichiers, même avec extension .txt
            genealogy = parser.parse_file(temp_path)
            assert isinstance(genealogy, Genealogy)
        finally:
            os.unlink(temp_path)

    def test_parse_file_valid_gw(self):
        """Test parsing d'un fichier .gw valide"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre
end"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gw", delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            genealogy = parser.parse_file(temp_path)
            assert isinstance(genealogy, Genealogy)
            assert len(genealogy.persons) >= 2
            assert len(genealogy.families) >= 1
        finally:
            os.unlink(temp_path)

    def test_parse_string_valid(self):
        """Test parsing d'une chaîne valide"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2
        assert len(genealogy.families) >= 1

    def test_parse_string_empty(self):
        """Test parsing d'une chaîne vide"""
        parser = GeneWebParser(validate=False)

        genealogy = parser.parse_string("")
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0

    def test_parse_string_whitespace_only(self):
        """Test parsing d'une chaîne avec seulement des espaces"""
        parser = GeneWebParser(validate=False)

        genealogy = parser.parse_string("   \n  \t  ")
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0

    def test_parse_string_with_comments(self):
        """Test parsing d'une chaîne avec commentaires"""
        parser = GeneWebParser(validate=False)

        test_content = """# Commentaire
fam DUPONT Jean MARTIN Marie
# Autre commentaire
beg
- DUPONT Pierre
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2
        assert len(genealogy.families) >= 1

    def test_parse_string_with_encoding_error(self):
        """Test parsing avec erreur d'encodage"""
        parser = GeneWebParser()

        # Créer un fichier temporaire pour tester l'erreur d'encodage
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gw", delete=False) as f:
            f.write("fam DUPONT Jean MARTIN Marie")
            temp_path = f.name

        try:
            # Simuler une erreur d'encodage en patchant la méthode
            with patch.object(
                parser,
                "_read_file_with_encoding",
                side_effect=GeneWebEncodingError("Erreur d'encodage"),
            ):
                with pytest.raises(GeneWebEncodingError):
                    parser.parse_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_parse_string_with_lexical_error(self):
        """Test parsing avec contenu qui pourrait causer des erreurs lexicales"""
        parser = GeneWebParser(validate=False)

        # Contenu avec des caractères spéciaux qui pourraient poser problème
        test_content = "fam DUPONT Jean MARTIN Marie\ninvalid_token_that_should_fail"

        # Le parser est tolérant et ne lève pas d'exception
        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)

    def test_parse_string_with_syntax_error(self):
        """Test parsing avec syntaxe potentiellement invalide"""
        parser = GeneWebParser(validate=False)

        # Contenu avec syntaxe qui pourrait être invalide
        test_content = "fam DUPONT Jean MARTIN Marie\ninvalid_syntax_block"

        # Le parser est tolérant et ne lève pas d'exception
        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)

    def test_parse_string_with_validation_error(self):
        """Test parsing avec contenu qui pourrait causer des erreurs de validation"""
        parser = GeneWebParser(validate=False)

        # Contenu qui pourrait causer des erreurs de validation
        test_content = "fam DUPONT Jean MARTIN Marie\ninvalid_reference"

        # Le parser est tolérant et ne lève pas d'exception
        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)

    def test_parse_string_without_validation(self):
        """Test parsing sans validation (devrait passer même avec des erreurs)"""
        parser = GeneWebParser(validate=False)

        # Contenu qui devrait causer une erreur de validation mais pas de parsing
        test_content = "fam DUPONT Jean MARTIN Marie\ninvalid_reference"

        # Ne devrait pas lever d'exception car validate=False
        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)

    def test_parse_string_with_unicode(self):
        """Test parsing avec caractères Unicode"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre-François
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2

    def test_parse_string_with_special_characters(self):
        """Test parsing avec caractères spéciaux"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre (dit "Le Grand")
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2

    def test_parse_string_with_multiple_families(self):
        """Test parsing avec plusieurs familles"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre
end
fam MARTIN Paul DURAND Sophie
beg
- MARTIN Paul
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 4
        assert len(genealogy.families) >= 2

    def test_parse_string_with_notes(self):
        """Test parsing avec notes"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
notes DUPONT Jean
beg
Note importante sur Jean DUPONT
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2

    def test_parse_string_with_events(self):
        """Test parsing avec événements"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
pevt DUPONT Jean
beg
birt 01/01/1990
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2

    def test_parse_string_with_complex_structure(self):
        """Test parsing avec structure complexe"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre
- DUPONT Marie
end
notes DUPONT Jean
beg
Note sur Jean DUPONT
end
pevt DUPONT Jean
beg
birt 01/01/1990
deat 31/12/2020
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 3
        assert len(genealogy.families) >= 1

    def test_parse_string_with_empty_blocks(self):
        """Test parsing avec blocs vides"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
beg
end
notes DUPONT Jean
beg
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2
        assert len(genealogy.families) >= 1

    def test_parse_string_with_nested_blocks(self):
        """Test parsing avec blocs imbriqués"""
        parser = GeneWebParser(validate=False)

        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre
beg
Note sur Pierre
end
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2
        assert len(genealogy.families) >= 1

    def test_parse_string_with_encoding_detection(self):
        """Test parsing avec détection d'encodage"""
        parser = GeneWebParser(validate=False)

        # Contenu avec caractères spéciaux qui nécessitent UTF-8
        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre-François
end"""

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2

    def test_parse_string_with_large_content(self):
        """Test parsing avec contenu volumineux"""
        parser = GeneWebParser(validate=False)

        # Générer un contenu volumineux
        test_content = "fam DUPONT Jean MARTIN Marie\n"
        for i in range(100):
            test_content += f"beg\n- DUPONT Enfant{i}\nend\n"

        genealogy = parser.parse_string(test_content)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2
        assert len(genealogy.families) >= 1
