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
        assert date.text_date == "0"
    
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
        assert date.display_text == "0(0)"  # Format avec parenthèses


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
