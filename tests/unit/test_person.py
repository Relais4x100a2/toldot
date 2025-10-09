"""
Tests unitaires pour le modèle Person

Ces tests vérifient la création et manipulation des personnes
dans le format GeneWeb.
"""

import pytest
from geneweb_py.core.person import Person, Title, Gender, AccessLevel
from geneweb_py.core.date import Date


class TestPersonCreation:
    """Tests pour la création de personnes"""

    def test_create_simple_person(self):
        """Test création d'une personne simple"""
        person = Person(last_name="CORNO", first_name="Joseph")

        assert person.last_name == "CORNO"
        assert person.first_name == "Joseph"
        assert person.occurrence_number == 0
        assert person.gender == Gender.UNKNOWN
        assert person.full_name == "CORNO Joseph"
        assert person.unique_id == "CORNO_Joseph_0"

    def test_create_person_with_occurrence(self):
        """Test création avec numéro d'occurrence"""
        person = Person(last_name="CORNO", first_name="Joseph", occurrence_number=1)

        assert person.occurrence_number == 1
        assert person.full_name == "CORNO Joseph .1"  # Espace avant le point
        assert person.unique_id == "CORNO_Joseph_1"

    def test_create_person_with_dates(self):
        """Test création avec dates"""
        birth_date = Date.parse("25/12/1990")
        death_date = Date.parse("10/01/2020")

        person = Person(
            last_name="CORNO",
            first_name="Joseph",
            birth_date=birth_date,
            death_date=death_date,
        )

        assert person.birth_date == birth_date
        assert person.death_date == death_date
        assert person.age_at_death == 30

    def test_name_normalization(self):
        """Test normalisation des noms (espaces -> underscores)"""
        person = Person(last_name="DE LA ROCHE", first_name="Jean Pierre")

        assert person.last_name == "DE_LA_ROCHE"
        assert person.first_name == "Jean_Pierre"


class TestPersonProperties:
    """Tests pour les propriétés des personnes"""

    def test_display_name_with_public_name(self):
        """Test nom d'affichage avec nom public"""
        person = Person(
            last_name="CORNO", first_name="Joseph_Marie_Vincent", public_name="Joseph"
        )

        assert person.display_name == "CORNO Joseph"

    def test_display_name_without_public_name(self):
        """Test nom d'affichage sans nom public"""
        person = Person(last_name="CORNO", first_name="Joseph")

        assert person.display_name == "CORNO Joseph"

    def test_is_alive_with_death_date(self):
        """Test statut vivant avec date de décès"""
        person = Person(
            last_name="CORNO", first_name="Joseph", death_date=Date.parse("10/01/2020")
        )

        assert person.is_alive is False

    def test_is_alive_without_death_date(self):
        """Test statut vivant sans date de décès"""
        person = Person(
            last_name="CORNO", first_name="Joseph", birth_date=Date.parse("25/12/1990")
        )

        assert person.is_alive is True

    def test_is_alive_obviously_dead(self):
        """Test statut vivant avec tag #od"""
        person = Person(last_name="CORNO", first_name="Joseph", is_obviously_dead=True)

        assert person.is_alive is False


class TestPersonValidation:
    """Tests pour la validation des personnes"""

    def test_invalid_birth_death_dates(self):
        """Test dates incohérentes (naissance > décès)"""
        person = Person(
            last_name="CORNO",
            first_name="Joseph",
            birth_date=Date.parse("25/12/1990"),
            death_date=Date.parse("10/01/1980"),  # Avant la naissance
        )
        # Vérifier qu'une erreur de validation a été ajoutée
        assert len(person.validation_errors) > 0
        assert any("postérieure" in str(err) for err in person.validation_errors)


class TestPersonMethods:
    """Tests pour les méthodes des personnes"""

    def test_add_title(self):
        """Test ajout de titre"""
        person = Person(last_name="CORNO", first_name="Joseph")

        title = Title(name="Comte", title_type="Noblesse", place="France")

        person.add_title(title)
        assert len(person.titles) == 1
        assert person.titles[0] == title

    def test_add_note(self):
        """Test ajout de note"""
        person = Person(last_name="CORNO", first_name="Joseph")

        person.add_note("Note importante")
        assert len(person.notes) == 1
        assert person.notes[0] == "Note importante"

    def test_add_relation(self):
        """Test ajout de relation"""
        person = Person(last_name="CORNO", first_name="Joseph")

        person.add_relation("adop", "PARENT_Jean_0")
        assert "adop" in person.relations
        assert "PARENT_Jean_0" in person.relations["adop"]


class TestPersonSerialization:
    """Tests pour la sérialisation des personnes"""

    def test_to_dict(self):
        """Test conversion en dictionnaire"""
        person = Person(
            last_name="CORNO",
            first_name="Joseph",
            gender=Gender.MALE,
            birth_date=Date.parse("25/12/1990"),
            birth_place="Paris",
        )

        data = person.to_dict()

        assert data["last_name"] == "CORNO"
        assert data["first_name"] == "Joseph"
        assert data["gender"] == "m"
        assert data["birth_place"] == "Paris"
        assert "unique_id" in data
        assert "full_name" in data


class TestTitle:
    """Tests pour les titres"""

    def test_title_creation(self):
        """Test création de titre"""
        title = Title(
            name="Comte", title_type="Noblesse", place="France", number=1, is_main=True
        )

        assert title.name == "Comte"
        assert title.title_type == "Noblesse"
        assert title.place == "France"
        assert title.number == 1
        assert title.is_main is True

    def test_title_string_representation(self):
        """Test représentation string du titre"""
        title = Title(name="Comte", title_type="Noblesse", place="France")

        expected = "Comte:Noblesse:France::"
        assert str(title) == expected
