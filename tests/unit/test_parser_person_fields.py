"""
Tests unitaires pour le parsing des champs sources et lieux personnels

Ces tests vérifient le parsing des modificateurs #bs, #ds, #pp, #ps, #rp, #rs
dans les informations personnelles inline.
"""

from geneweb_py.core.parser import GeneWebParser


class TestPersonSourcePlaceFields:
    """Tests pour les champs sources et lieux de personnes"""

    def test_birth_source(self):
        """Test parsing de #bs (source de naissance)"""
        content = "fam DUPONT Jean 1750 #bs Archives_de_Paris\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.birth_source == "Archives de Paris"

    def test_death_source(self):
        """Test parsing de #ds (source de décès)"""
        content = "fam DUPONT Jean 0 1800 #ds Registre_Civil\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.death_source == "Registre Civil"

    def test_baptism_place(self):
        """Test parsing de #pp (lieu baptême)"""
        content = "fam DUPONT Jean 1750 #pp Eglise_Saint-Nicolas\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.baptism_place is not None
        assert "Saint-Nicolas" in jean.baptism_place

    def test_baptism_source(self):
        """Test parsing de #ps (source baptême)"""
        content = "fam DUPONT Jean 1750 #ps Archives_Diocesaines\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.baptism_source is not None

    def test_burial_place(self):
        """Test parsing de #rp (lieu inhumation)"""
        content = "fam DUPONT Jean 0 1800 #rp Cimetiere_du_Pere-Lachaise\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.burial_place is not None

    def test_burial_source(self):
        """Test parsing de #rs (source inhumation)"""
        content = "fam DUPONT Jean 0 1800 #rs Acte_de_Deces\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.burial_source is not None


class TestPersonNameSyntax:
    """Tests pour les noms publics et alias de prénoms"""

    def test_public_name(self):
        """Test parsing de (PublicName)"""
        content = "fam DUPONT Jean (Jean_le_Grand) 1750 + MARTIN Marie\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean" and p.last_name == "DUPONT"
        )
        assert jean is not None
        assert jean.public_name == "Jean le Grand"

    def test_first_name_alias(self):
        """Test parsing de {FirstNameAlias}"""
        content = "fam DUPONT Jean {Jeannot} 1750 + MARTIN Marie\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert jean.first_name_alias == "Jeannot"

    def test_unclosed_paren_no_crash(self):
        """Une parenthèse non fermée ne doit pas lever IndexError."""
        content = "fam DUPONT (Jean_incomplet 1750 + MARTIN Marie\n"
        genealogy = GeneWebParser().parse_string(content)
        assert genealogy is not None

    def test_unclosed_brace_no_crash(self):
        """Une accolade non fermée ne doit pas lever IndexError."""
        content = "fam DUPONT Jean {Alias_incomplet 1750 + MARTIN Marie\n"
        genealogy = GeneWebParser().parse_string(content)
        assert genealogy is not None


class TestPersonTitles:
    """Tests pour le parsing des titres de noblesse"""

    def test_full_title(self):
        """Test parsing d'un titre complet [*:Comte:Paris:1720:1740:2]"""
        content = "fam DUPONT Jean [*:Comte:Paris:1720:1740:2] 1700 + MARTIN Marie\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert len(jean.titles) == 1
        t = jean.titles[0]
        assert t.is_main is True
        assert t.title_type == "Comte"
        assert t.place == "Paris"
        assert t.number == 2

    def test_partial_title_defaults(self):
        """Test parsing d'un titre partiel [:Baron::1800::]"""
        content = "fam DUPONT Jean [:Baron::1800::] 1780 + MARTIN Marie\n"
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert len(jean.titles) == 1
        t = jean.titles[0]
        assert t.title_type == "Baron"
        assert t.number == 1  # default

    def test_multiple_titles(self):
        """Test parsing de plusieurs titres"""
        content = (
            "fam DUPONT Jean [*:Roi:France:::] [:Duc:Paris:::] 1750"
            " + MARTIN Marie\n"
        )
        genealogy = GeneWebParser().parse_string(content)
        jean = next(
            p for p in genealogy.persons.values()
            if p.first_name == "Jean"
        )
        assert len(jean.titles) == 2

    def test_unclosed_bracket_no_crash(self):
        """Un crochet non fermé ne doit pas lever d'erreur."""
        content = "fam DUPONT Jean [*:Comte 1700 + MARTIN Marie\n"
        genealogy = GeneWebParser().parse_string(content)
        assert genealogy is not None
