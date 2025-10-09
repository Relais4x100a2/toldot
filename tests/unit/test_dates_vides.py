"""
Tests pour la gestion des dates vides dans le parser GeneWeb
"""

import pytest
from geneweb_py.core.date import Date, DatePrefix
from geneweb_py.core.parser.gw_parser import GeneWebParser


class TestDatesVides:
    """Tests pour la gestion des dates vides"""

    def test_date_vide_retourne_inconnue(self):
        """Test qu'une date vide retourne une date inconnue"""
        date = Date.parse("")
        assert date.is_unknown is True
        assert date.display_text == "0"

    def test_date_espaces_retourne_inconnue(self):
        """Test qu'une date avec seulement des espaces retourne une date inconnue"""
        date = Date.parse("   ")
        assert date.is_unknown is True
        assert date.display_text == "0"

    def test_parse_with_fallback_date_vide(self):
        """Test que parse_with_fallback gère les dates vides"""
        date = Date.parse_with_fallback("")
        assert date.is_unknown is True
        assert date.display_text == "0"

    def test_parse_with_fallback_date_invalide(self):
        """Test que parse_with_fallback gère les dates invalides"""
        date = Date.parse_with_fallback("date_invalide")
        assert date.is_unknown is True
        assert date.display_text == "0"

    def test_parse_with_fallback_date_valide(self):
        """Test que parse_with_fallback gère les dates valides"""
        date = Date.parse_with_fallback("25/12/1990")
        assert date.is_unknown is False
        assert date.day == 25
        assert date.month == 12
        assert date.year == 1990
        assert date.display_text == "25/12/1990"


class TestParserDatesVides:
    """Tests pour le parser avec des dates vides"""

    def test_parser_pevt_avec_date_deces_vide(self):
        """Test le parsing d'un bloc pevt avec date de décès vide"""
        content = """pevt PETIT Louis_Pierre
#birt 12/3/1884 #p Arras,_62041,_Pas-de-Calais,_Nord-Pas-de-Calais,_France
#deat
end pevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'une personne a été créée
        assert len(genealogy.persons) == 1

        person = list(genealogy.persons.values())[0]
        assert person.last_name == "PETIT"
        assert person.first_name == "Louis_Pierre"

        # Vérifier la date de naissance
        assert person.birth_date is not None
        assert person.birth_date.day == 12
        assert person.birth_date.month == 3
        assert person.birth_date.year == 1884

        # Vérifier que la date de décès est inconnue
        assert person.death_date is not None
        assert person.death_date.is_unknown is True

    def test_parser_pevt_avec_date_naissance_vide(self):
        """Test le parsing d'un bloc pevt avec date de naissance vide"""
        content = """pevt DE_BONNIVAL Louise
#birt
#deat 15/8/1940 #p Lyon,_69001,_Rhône,_Auvergne-Rhône-Alpes,_France
end pevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'une personne a été créée
        assert len(genealogy.persons) == 1

        person = list(genealogy.persons.values())[0]
        assert person.last_name == "DE_BONNIVAL"
        assert person.first_name == "Louise"

        # Vérifier que la date de naissance est inconnue
        assert person.birth_date is not None
        assert person.birth_date.is_unknown is True

        # Vérifier la date de décès
        assert person.death_date is not None
        assert person.death_date.day == 15
        assert person.death_date.month == 8
        assert person.death_date.year == 1940

    def test_parser_pevt_avec_dates_vides(self):
        """Test le parsing d'un bloc pevt avec toutes les dates vides"""
        content = """pevt SIMON Henriette
#birt
#deat
end pevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'une personne a été créée
        assert len(genealogy.persons) == 1

        person = list(genealogy.persons.values())[0]
        assert person.last_name == "CONSTANT"
        assert person.first_name == "Henriette"

        # Vérifier que les dates sont inconnues
        assert person.birth_date is not None
        assert person.birth_date.is_unknown is True
        assert person.death_date is not None
        assert person.death_date.is_unknown is True

    def test_parser_pevt_avec_date_bapteme_vide(self):
        """Test le parsing d'un bloc pevt avec date de baptême vide"""
        content = """pevt ROBERT Hélène
#birt 2/4/1895 #p Beuvry,_62126,_Pas-de-Calais,_Nord-Pas-de-Calais,_France
#bapt
#deat
end pevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'une personne a été créée
        assert len(genealogy.persons) == 1

        person = list(genealogy.persons.values())[0]
        assert person.last_name == "ROBERT"
        assert person.first_name == "Hélène"

        # Vérifier la date de naissance
        assert person.birth_date is not None
        assert person.birth_date.day == 2
        assert person.birth_date.month == 4
        assert person.birth_date.year == 1895

        # Vérifier que la date de décès est inconnue
        assert person.death_date is not None
        assert person.death_date.is_unknown is True

        # Vérifier qu'il n'y a pas d'événement de baptême (date vide)
        baptism_events = [e for e in person.events if e.event_type.value == "baptism"]
        assert len(baptism_events) == 0
