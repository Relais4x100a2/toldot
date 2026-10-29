"""
Tests d'intégration pour les parsers
"""

import os
import tempfile

from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.parser.gw_parser import GeneWebParser


class TestParserIntegration:
    """Tests d'intégration pour les parsers."""

    def test_parse_simple_family_integration(self):
        """Test parsing d'une famille simple avec intégration complète."""
        test_content = """fam DUPONT Jean MARTIN Marie
end fam"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1  # Au moins 1 personne
        assert len(genealogy.families) >= 1  # Au moins 1 famille

    def test_parse_person_with_events_integration(self):
        """Test parsing d'une personne avec événements."""
        test_content = """pevt DUPONT Jean
#birt 15/6/1990 #p Paris
#deat 20/8/2020 #p Lyon
end pevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1

    def test_parse_family_with_events_integration(self):
        """Test parsing d'une famille avec événements."""
        test_content = """fam DUPONT Jean MARTIN Marie
#marr 10/5/2015 #p Marseille
#div 15/3/2020 #p Nice
end fam"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1

    def test_parse_notes_integration(self):
        """Test parsing de notes."""
        test_content = """notes DUPONT Jean
Note personnelle importante
avec plusieurs lignes
end notes"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1

    def test_parse_relations_integration(self):
        """Test parsing de relations."""
        test_content = """fam DUPONT Jean MARTIN Marie
#adop
end fam"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1

    def test_parse_complex_genealogy_integration(self):
        """Test parsing d'une généalogie complexe."""
        test_content = """fam DUPONT Jean MARTIN Marie
beg
- DUPONT Pierre
end
end fam

fam MARTIN Pierre DUPONT Anne
end fam"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 2
        assert len(genealogy.families) >= 2

    def test_parse_with_validation_integration(self):
        """Test parsing avec validation activée."""
        test_content = """fam DUPONT Jean MARTIN Marie
end fam"""

        parser = GeneWebParser(validate=True)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1
        assert len(genealogy.families) >= 1

    def test_parse_file_integration(self):
        """Test parsing d'un fichier avec intégration complète."""
        test_content = """fam DUPONT Jean MARTIN Marie
end fam"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gw", delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            parser = GeneWebParser(validate=False)
            genealogy = parser.parse_file(temp_path)

            assert isinstance(genealogy, Genealogy)
            assert len(genealogy.persons) >= 2
            assert len(genealogy.families) >= 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_parse_empty_content_integration(self):
        """Test parsing de contenu vide."""
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string("")

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0

    def test_parse_whitespace_only_integration(self):
        """Test parsing de contenu avec seulement des espaces."""
        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string("   \n\n   \n   ")

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0

    def test_parse_with_comments_integration(self):
        """Test parsing avec commentaires."""
        test_content = """# Commentaire de début
fam DUPONT Jean MARTIN Marie
# Commentaire dans la famille
end fam
# Commentaire de fin"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1
        assert len(genealogy.families) >= 1

    def test_parse_multiple_blocks_integration(self):
        """Test parsing de plusieurs blocs différents."""
        test_content = """fam DUPONT Jean
husb DUPONT Jean
end fam

notes MARTIN Marie
Note personnelle
end notes

pevt DUPONT Jean
#birt 15/6/1990
end pevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(test_content)

        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) >= 1
        assert len(genealogy.families) >= 1
