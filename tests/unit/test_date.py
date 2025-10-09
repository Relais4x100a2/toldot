"""
Tests unitaires pour le modèle Date

Ces tests vérifient le parsing et la manipulation des dates
au format GeneWeb.
"""

import pytest
from geneweb_py.core.date import Date, DatePrefix, CalendarType, DeathType


class TestDateParsing:
    """Tests pour le parsing des dates"""

    def test_parse_simple_date(self):
        """Test parsing d'une date simple dd/mm/yyyy"""
        date = Date.parse("25/12/1990")
        assert date.day == 25
        assert date.month == 12
        assert date.year == 1990
        assert date.prefix is None
        assert date.calendar == CalendarType.GREGORIAN

    def test_parse_month_year(self):
        """Test parsing d'une date mois/année"""
        date = Date.parse("12/1990")
        assert date.day is None
        assert date.month == 12
        assert date.year == 1990

    def test_parse_year_only(self):
        """Test parsing d'une année seule"""
        date = Date.parse("1990")
        assert date.day is None
        assert date.month is None
        assert date.year == 1990

    def test_parse_unknown_date(self):
        """Test parsing d'une date inconnue"""
        date = Date.parse("0")
        assert date.is_unknown is True
        assert date.text_date is None

    def test_parse_text_date(self):
        """Test parsing d'une date textuelle"""
        date = Date.parse("0(5_Mai_1990)")
        assert date.text_date == "5_Mai_1990"
        assert date.day is None
        assert date.month is None
        assert date.year is None


class TestDatePrefixes:
    """Tests pour les préfixes de date"""

    def test_about_prefix(self):
        """Test préfixe 'about' (~)"""
        date = Date.parse("~10/5/1990")
        assert date.prefix == DatePrefix.ABOUT
        assert date.day == 10
        assert date.month == 5
        assert date.year == 1990

    def test_maybe_prefix(self):
        """Test préfixe 'maybe' (?)"""
        date = Date.parse("?10/5/1990")
        assert date.prefix == DatePrefix.MAYBE

    def test_before_prefix(self):
        """Test préfixe 'before' (<)"""
        date = Date.parse("<10/5/1990")
        assert date.prefix == DatePrefix.BEFORE

    def test_after_prefix(self):
        """Test préfixe 'after' (>)"""
        date = Date.parse(">10/5/1990")
        assert date.prefix == DatePrefix.AFTER


class TestDateCalendars:
    """Tests pour les calendriers"""

    def test_julian_calendar(self):
        """Test calendrier julien"""
        date = Date.parse("10/9/5750J")
        assert date.calendar == CalendarType.JULIAN
        assert date.year == 5750

    def test_french_republican_calendar(self):
        """Test calendrier républicain français"""
        date = Date.parse("10/9/5750F")
        assert date.calendar == CalendarType.FRENCH_REPUBLICAN

    def test_hebrew_calendar(self):
        """Test calendrier hébreu"""
        date = Date.parse("10/9/5750H")
        assert date.calendar == CalendarType.HEBREW


class TestDeathTypes:
    """Tests pour les types de décès"""

    def test_killed_death(self):
        """Test décès par meurtre"""
        date = Date.parse("k10/5/1990")
        assert date.death_type == DeathType.KILLED

    def test_murdered_death(self):
        """Test décès par assassinat"""
        date = Date.parse("m10/5/1990")
        assert date.death_type == DeathType.MURDERED

    def test_executed_death(self):
        """Test décès par exécution"""
        date = Date.parse("e10/5/1990")
        assert date.death_type == DeathType.EXECUTED

    def test_disappeared_death(self):
        """Test décès par disparition"""
        date = Date.parse("s10/5/1990")
        assert date.death_type == DeathType.DISAPPEARED


class TestDateDisplay:
    """Tests pour l'affichage des dates"""

    def test_display_simple_date(self):
        """Test affichage d'une date simple"""
        date = Date.parse("25/12/1990")
        assert date.display_text == "25/12/1990"

    def test_display_date_with_prefix(self):
        """Test affichage avec préfixe"""
        date = Date.parse("~10/5/1990")
        assert date.display_text == "~10/05/1990"  # Format avec zéro padding

    def test_display_text_date(self):
        """Test affichage date textuelle"""
        date = Date.parse("0(5_Mai_1990)")
        assert date.display_text == "0(5_Mai_1990)"

    def test_display_unknown_date(self):
        """Test affichage date inconnue"""
        date = Date.parse("0")
        assert date.display_text == "0"  # Format simple pour date inconnue


class TestDateValidation:
    """Tests pour la validation des dates"""

    def test_invalid_day(self):
        """Test jour invalide"""
        with pytest.raises(ValueError):
            Date(day=32, month=12, year=1990)

    def test_invalid_month(self):
        """Test mois invalide"""
        with pytest.raises(ValueError):
            Date(day=25, month=13, year=1990)

    def test_invalid_year(self):
        """Test année invalide"""
        with pytest.raises(ValueError):
            Date(day=25, month=12, year=0)


class TestDateEmptyFields:
    """Tests pour la gestion des champs vides dans les dates"""

    def test_empty_string(self):
        """Test chaîne vide"""
        date = Date.parse("")
        assert date.is_unknown is True

    def test_whitespace_only(self):
        """Test espaces seulement"""
        date = Date.parse("   ")
        assert date.is_unknown is True

    def test_none_input(self):
        """Test entrée None"""
        date = Date.parse(None)
        assert date.is_unknown is True

    def test_empty_slashes(self):
        """Test slashes vides (//)"""
        date = Date.parse("//")
        assert date.is_unknown is True

    def test_empty_month(self):
        """Test mois vide (/1990)"""
        date = Date.parse("/1990")
        assert date.year == 1990
        assert date.month is None
        assert date.day is None
        assert date.is_unknown is False

    def test_empty_month_middle(self):
        """Test mois vide au milieu (25//1990)"""
        date = Date.parse("25//1990")
        assert date.day == 25
        assert date.year == 1990
        assert date.month is None
        assert date.is_unknown is False

    def test_empty_year(self):
        """Test année vide (25/12/)"""
        date = Date.parse("25/12/")
        assert date.day == 25
        assert date.month == 12
        assert date.year is None
        assert date.is_unknown is False

    def test_prefix_with_empty_fields(self):
        """Test préfixes avec champs vides"""
        # Préfixe avec jour et mois vides
        date = Date.parse("~//1990")
        assert date.prefix == DatePrefix.ABOUT
        assert date.year == 1990
        assert date.day is None
        assert date.month is None

        # Préfixe avec jour et année vides
        date = Date.parse("?/12/")
        assert date.prefix == DatePrefix.MAYBE
        assert date.month == 12
        assert date.day is None
        assert date.year is None

        # Préfixe avec mois et année vides
        date = Date.parse("<25//")
        assert date.prefix == DatePrefix.BEFORE
        assert date.day == 25
        assert date.month is None
        assert date.year is None

    def test_decimal_year(self):
        """Test année décimale (1990.5)"""
        date = Date.parse("1990.5")
        assert date.year == 1990
        assert date.day is None
        assert date.month is None
        assert date.is_unknown is False

    def test_invalid_format_still_fails(self):
        """Test que les formats vraiment invalides échouent toujours"""
        with pytest.raises(ValueError):
            Date.parse("invalid")

        with pytest.raises(ValueError):
            Date.parse("1990-12")  # Format avec tiret non supporté


class TestDateAlternatives:
    """Tests pour les dates alternatives (OR et BETWEEN)"""

    def test_or_dates_with_year(self):
        """Test 'OR' entre une date complète et une année"""
        date = Date.parse("10/5/1990|1991")
        assert date.prefix == DatePrefix.OR
        assert date.day == 10 and date.month == 5 and date.year == 1990
        assert len(date.alternative_dates) == 1
        assert date.alternative_dates[0].year == 1991
        assert date.display_text == "10/05/1990|1991"

    def test_between_dates_years(self):
        """Test 'BETWEEN' entre deux années"""
        date = Date.parse("1990..1995")
        assert date.prefix == DatePrefix.BETWEEN
        assert date.year == 1990
        assert len(date.alternative_dates) == 1
        assert date.alternative_dates[0].year == 1995
        assert date.display_text == "1990..1995"


class TestDateProperties:
    """Tests pour les propriétés des dates"""

    def test_is_complete(self):
        """Test propriété is_complete"""
        complete_date = Date(day=25, month=12, year=1990)
        assert complete_date.is_complete is True

        partial_date = Date(month=12, year=1990)
        assert partial_date.is_complete is False

    def test_is_partial(self):
        """Test propriété is_partial"""
        partial_date = Date(month=12, year=1990)
        assert partial_date.is_partial is True

        complete_date = Date(day=25, month=12, year=1990)
        assert complete_date.is_partial is False

    def test_to_iso_format(self):
        """Test conversion ISO"""
        date = Date.parse("25/12/1990")
        assert date.to_iso_format() == "1990-12-25"

        partial_date = Date.parse("12/1990")
        assert partial_date.to_iso_format() is None


class TestDateComparisons:
    """Tests pour les méthodes de comparaison de dates."""

    def test_is_after_different_years(self):
        """Test is_after avec années différentes."""
        date1 = Date(year=2000)
        date2 = Date(year=1990)
        assert date1.is_after(date2) is True
        assert date2.is_after(date1) is False

    def test_is_after_same_year_different_months(self):
        """Test is_after même année, mois différents."""
        date1 = Date(year=2000, month=6)
        date2 = Date(year=2000, month=3)
        assert date1.is_after(date2) is True
        assert date2.is_after(date1) is False

    def test_is_after_same_date(self):
        """Test is_after avec dates identiques."""
        date1 = Date(year=2000, month=6, day=15)
        date2 = Date(year=2000, month=6, day=15)
        assert date1.is_after(date2) is False

    def test_is_after_unknown(self):
        """Test is_after avec date inconnue."""
        date1 = Date(is_unknown=True)
        date2 = Date(year=2000)
        assert date1.is_after(date2) is False
        assert date2.is_after(date1) is False

    def test_is_before_different_years(self):
        """Test is_before avec années différentes."""
        date1 = Date(year=1990)
        date2 = Date(year=2000)
        assert date1.is_before(date2) is True
        assert date2.is_before(date1) is False

    def test_is_before_same_year_different_months(self):
        """Test is_before même année, mois différents."""
        date1 = Date(year=2000, month=3)
        date2 = Date(year=2000, month=6)
        assert date1.is_before(date2) is True

    def test_is_before_unknown(self):
        """Test is_before avec date inconnue."""
        date1 = Date(is_unknown=True)
        date2 = Date(year=2000)
        assert date1.is_before(date2) is False

        """Test méthode __str__."""
        date = Date(year=1950, month=3, day=15)
        result = str(date)
        assert isinstance(result, str)
