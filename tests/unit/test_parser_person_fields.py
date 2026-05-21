"""Tests des champs de personne ajoutés en Phase 2."""


from geneweb_py.core.parser.gw_parser import GeneWebParser


class TestPersonAliasFields:
    """Tests pour les champs alias et image (#nick, #salias, #alias, #image)"""

    def test_nick(self) -> None:
        """Test parsing du surnom (#nick)"""
        content = "fam DUPONT Jean #nick LeGrand\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.nickname == "LeGrand"

    def test_salias(self) -> None:
        """Test parsing de l'alias de nom (#salias)"""
        content = "fam DUPONT Jean #salias DuPlessis\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.surname_alias == "DuPlessis"

    def test_alias(self) -> None:
        """Test parsing de l'alias général (#alias)"""
        content = "fam DUPONT Jean #alias JeanJean\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.general_alias == "JeanJean"

    def test_image(self) -> None:
        """Test parsing du chemin image (#image)"""
        content = "fam DUPONT Jean #image /photos/jean.jpg\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.image_path == "/photos/jean.jpg"

    def test_combined_aliases(self) -> None:
        """Test parsing de multiples alias sur une même personne"""
        content = "fam DUPONT Jean #nick LeGrand #salias DuPont #alias JD\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.nickname == "LeGrand"
        assert jean.surname_alias == "DuPont"
        assert jean.general_alias == "JD"

    def test_nick_with_underscores(self) -> None:
        """Test que les underscores dans les surnoms sont remplacés par des espaces"""
        content = "fam DUPONT Jean #nick Le_Grand\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.nickname == "Le Grand"

    def test_image_with_complex_path(self) -> None:
        """Test parsing d'un chemin image complexe"""
        content = "fam DUPONT Jean #image /photos/2024/family/jean.png\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.image_path == "/photos/2024/family/jean.png"

    def test_all_fields_together(self) -> None:
        """Test parsing de tous les champs alias + image ensemble"""
        content = (
            "fam DUPONT Jean #nick LeGrand #salias DuPont "
            "#alias JD #image /photos/jean.jpg\n"
        )
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.nickname == "LeGrand"
        assert jean.surname_alias == "DuPont"
        assert jean.general_alias == "JD"
        assert jean.image_path == "/photos/jean.jpg"

    def test_spouse_with_aliases(self) -> None:
        """Test que les aliases fonctionnent aussi pour l'épouse"""
        content = (
            "fam DUPONT Jean +MARTIN Marie #nick LaReine "
            "#alias MM\n"
        )
        genealogy = GeneWebParser().parse_string(content)
        marie = next(
            p
            for p in genealogy.persons.values()
            if p.first_name == "Marie"
        )
        assert marie.nickname == "LaReine"
        assert marie.general_alias == "MM"
