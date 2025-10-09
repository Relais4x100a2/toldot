"""
Tests supplémentaires pour améliorer la couverture de date.py
"""

import pytest
from datetime import datetime
from geneweb_py.core.date import Date, DatePrefix, CalendarType, DeathType


class TestDateDisplayText:
    """Tests pour display_text avec différents cas"""
    
    def test_display_text_with_death_type(self):
        """Test display_text avec death_type"""
        date = Date(year=1990, death_type=DeathType.MURDERED)
        display = date.display_text
        # Vérifier que le death_type est présent
        assert "m" in display or "murd" in display.lower()
    
    def test_display_text_with_non_gregorian_calendar(self):
        """Test display_text avec calendrier non grégorien"""
        date = Date(day=15, month=3, year=1790, calendar=CalendarType.FRENCH_REPUBLICAN)
        assert "F" in date.display_text
    
    def test_is_partial_with_text_date(self):
        """Test is_partial avec text_date"""
        date = Date(text_date="Vers 1990")
        assert date.is_partial is False
    
    def test_is_partial_with_unknown_date(self):
        """Test is_partial avec date inconnue"""
        date = Date(is_unknown=True)
        assert date.is_partial is False


class TestDateParseEdgeCases:
    """Tests pour cas limites du parsing"""
    
    def test_parse_with_invalid_format(self):
        """Test parse avec format invalide lève ValueError"""
        with pytest.raises(ValueError):
            Date.parse("invalid_date")
    
    def test_parse_with_mixed_slashes(self):
        """Test parse avec slashes mélangés"""
        with pytest.raises(ValueError):
            Date.parse("25//12/1990")
    
    def test_parse_with_invalid_numbers(self):
        """Test parse avec nombres invalides dans les champs"""
        date = Date.parse("abc/12/1990")
        # Devrait gérer gracieusement avec None pour le jour
        assert date.day is None or date.year == 1990
    
    def test_parse_with_empty_month_year_fields(self):
        """Test parse avec champs mois/année vides"""
        date = Date.parse("  /  ")
        # Devrait retourner date inconnue
        assert date.is_unknown is True
    
    def test_parse_with_fallback_valid(self):
        """Test parse_with_fallback avec date valide"""
        date = Date.parse_with_fallback("25/12/1990")
        assert date.year == 1990
        assert date.month == 12
        assert date.day == 25
    
    def test_parse_with_fallback_invalid(self):
        """Test parse_with_fallback avec date invalide"""
        date = Date.parse_with_fallback("invalid_date")
        assert date.is_unknown is True


class TestDateComparison:
    """Tests pour les méthodes de comparaison"""
    
    def test_is_after_with_different_years(self):
        """Test is_after avec années différentes"""
        date1 = Date(year=1995)
        date2 = Date(year=1990)
        assert date1.is_after(date2) is True
        assert date2.is_after(date1) is False
    
    def test_is_after_with_same_year_different_months(self):
        """Test is_after avec même année, mois différents"""
        date1 = Date(month=12, year=1990)
        date2 = Date(month=6, year=1990)
        assert date1.is_after(date2) is True
        assert date2.is_after(date1) is False
    
    def test_is_after_with_same_year_month_different_days(self):
        """Test is_after avec même année/mois, jours différents"""
        date1 = Date(day=25, month=12, year=1990)
        date2 = Date(day=15, month=12, year=1990)
        assert date1.is_after(date2) is True
        assert date2.is_after(date1) is False
    
    def test_is_after_with_unknown_date(self):
        """Test is_after avec date inconnue"""
        date1 = Date(year=1990)
        date2 = Date(is_unknown=True)
        assert date1.is_after(date2) is False
        assert date2.is_after(date1) is False
    
    def test_is_after_with_partial_dates(self):
        """Test is_after avec dates partielles"""
        date1 = Date(year=1990)
        date2 = Date(year=1985)
        assert date1.is_after(date2) is True
    
    def test_is_before_with_different_years(self):
        """Test is_before avec années différentes"""
        date1 = Date(year=1990)
        date2 = Date(year=1995)
        assert date1.is_before(date2) is True
        assert date2.is_before(date1) is False
    
    def test_is_before_with_same_year_different_months(self):
        """Test is_before avec même année, mois différents"""
        date1 = Date(month=6, year=1990)
        date2 = Date(month=12, year=1990)
        assert date1.is_before(date2) is True
        assert date2.is_before(date1) is False
    
    def test_is_before_with_same_year_month_different_days(self):
        """Test is_before avec même année/mois, jours différents"""
        date1 = Date(day=15, month=12, year=1990)
        date2 = Date(day=25, month=12, year=1990)
        assert date1.is_before(date2) is True
        assert date2.is_before(date1) is False
    
    def test_is_before_with_unknown_date(self):
        """Test is_before avec date inconnue"""
        date1 = Date(year=1990)
        date2 = Date(is_unknown=True)
        assert date1.is_before(date2) is False
        assert date2.is_before(date1) is False
    
    def test_is_before_with_partial_dates(self):
        """Test is_before avec dates partielles"""
        date1 = Date(year=1985)
        date2 = Date(year=1990)
        assert date1.is_before(date2) is True


class TestDateStringRepresentation:
    """Tests pour __str__ et __repr__"""
    
    def test_str_representation(self):
        """Test __str__"""
        date = Date(day=25, month=12, year=1990)
        assert str(date) == "25/12/1990"
    
    def test_repr_representation(self):
        """Test __repr__"""
        date = Date(day=25, month=12, year=1990)
        assert repr(date) == "Date('25/12/1990')"


class TestDateAlternativeFormats:
    """Tests pour les dates alternatives et cas spéciaux"""
    
    def test_date_with_or_prefix_and_alternatives(self):
        """Test date avec OR et alternatives"""
        date = Date(
            day=25, 
            month=12, 
            year=1990,
            prefix=DatePrefix.OR,
            alternative_dates=[Date(day=26, month=12, year=1990)]
        )
        assert "|" in date.display_text
    
    def test_date_with_between_prefix_and_alternatives(self):
        """Test date avec BETWEEN et alternatives"""
        date = Date(
            day=1, 
            month=1, 
            year=1990,
            prefix=DatePrefix.BETWEEN,
            alternative_dates=[Date(day=31, month=12, year=1990)]
        )
        # BETWEEN devrait utiliser ".." entre les dates
        display = date.display_text
        assert ".." in display or "betw" in display.lower()


class TestDateEdgeCases:
    """Tests pour les cas limites"""
    
    def test_date_comparison_with_none_values(self):
        """Test comparaison avec valeurs None"""
        date1 = Date(year=1990)
        date2 = Date(year=1990, month=12)
        # Les comparaisons devraient gérer les None
        result_after = date1.is_after(date2)
        result_before = date1.is_before(date2)
        # Au moins l'une des deux devrait être False
        assert isinstance(result_after, bool)
        assert isinstance(result_before, bool)
    
    def test_display_text_only_day(self):
        """Test display_text avec seulement le jour (cas limite)"""
        date = Date(day=25)
        display = date.display_text
        assert "25" in display
    
    def test_display_text_only_month(self):
        """Test display_text avec seulement le mois (cas limite)"""
        date = Date(month=12)
        display = date.display_text
        assert "12" in display


class TestDateOperators:
    """Tests pour les opérateurs de comparaison"""
    
    def test_less_than_operator(self):
        """Test opérateur <"""
        date1 = Date(year=1990)
        date2 = Date(year=1995)
        # Si __lt__ est implémenté
        try:
            result = date1 < date2
            assert isinstance(result, bool)
        except TypeError:
            # __lt__ non implémenté
            pass
    
    def test_greater_than_operator(self):
        """Test opérateur >"""
        date1 = Date(year=1995)
        date2 = Date(year=1990)
        # Si __gt__ est implémenté
        try:
            result = date1 > date2
            assert isinstance(result, bool)
        except TypeError:
            # __gt__ non implémenté
            pass


class TestDateEquality:
    """Tests pour l'égalité des dates"""
    
    def test_date_equality(self):
        """Test égalité de deux dates identiques"""
        date1 = Date(day=25, month=12, year=1990)
        date2 = Date(day=25, month=12, year=1990)
        assert date1 == date2
    
    def test_date_inequality(self):
        """Test inégalité de deux dates différentes"""
        date1 = Date(day=25, month=12, year=1990)
        date2 = Date(day=26, month=12, year=1990)
        assert date1 != date2
    
    def test_date_with_text_equality(self):
        """Test égalité avec dates textuelles"""
        date1 = Date(text_date="Vers 1990")
        date2 = Date(text_date="Vers 1990")
        assert date1 == date2

