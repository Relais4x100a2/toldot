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
