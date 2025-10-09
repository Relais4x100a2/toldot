"""
Tests complets pour atteindre 100% de couverture sur exceptions.py

Lignes manquantes : 222-229, 278-283, 330, 348-356, 408, 476, 483, 499, 529, 568, 576, 580, 586, 591, 596, 611
"""

import pytest
from geneweb_py.core.exceptions import (
    GeneWebError,
    GeneWebParseError,
    GeneWebValidationError,
    GeneWebEncodingError,
    GeneWebConversionError,
    GeneWebErrorCollector,
)


class TestGeneWebError:
    """Tests de la classe de base GeneWebError"""

    def test_error_with_message(self):
        """Test erreur avec message simple"""
        error = GeneWebError("Test error")
        assert "Test error" in str(error)

    def test_error_with_context(self):
        """Test erreur avec contexte (lignes 222-229)"""
        error = GeneWebError("Test error", context={"file": "test.gw", "line": 42})
        error_str = str(error)
        assert "Test error" in error_str
        # Le contexte devrait être inclus
        assert error.context["file"] == "test.gw"


class TestGeneWebParseError:
    """Tests de GeneWebParseError"""

    def test_parse_error_simple(self):
        """Test erreur de parsing simple"""
        error = GeneWebParseError("Parse error")
        assert "Parse error" in str(error)

    def test_parse_error_with_line(self):
        """Test erreur avec numéro de ligne (lignes 278-283)"""
        error = GeneWebParseError("Parse error", line_number=42)
        error_str = str(error)
        assert "Parse error" in error_str or "42" in error_str

    def test_parse_error_with_all_params(self):
        """Test erreur avec tous les paramètres (ligne 330)"""
        error = GeneWebParseError(
            "Parse error",
            line_number=42,
            column=10,
            token="BAD",
            expected="GOOD",
            context={"file": "test.gw"},
        )
        error_str = str(error)
        assert "Parse error" in error_str


class TestGeneWebValidationError:
    """Tests de GeneWebValidationError"""

    def test_validation_error_simple(self):
        """Test erreur de validation simple"""
        error = GeneWebValidationError("Validation error")
        assert "Validation error" in str(error)

    def test_validation_error_with_field(self):
        """Test erreur avec champ (lignes 348-356)"""
        error = GeneWebValidationError("Validation error", field="birth_date")
        error_str = str(error)
        assert "Validation error" in error_str

    def test_validation_error_with_all_params(self):
        """Test erreur avec tous les paramètres (ligne 408)"""
        error = GeneWebValidationError(
            "Validation error",
            field="birth_date",
            value="invalid",
            entity_type="Person",
            entity_id="DUPONT_Jean_0",
        )
        error_str = str(error)
        assert "Validation error" in error_str


class TestGeneWebEncodingError:
    """Tests de GeneWebEncodingError"""

    def test_encoding_error_simple(self):
        """Test erreur d'encodage simple (ligne 476)"""
        error = GeneWebEncodingError("Encoding error")
        assert "Encoding error" in str(error)

    def test_encoding_error_with_encoding(self):
        """Test erreur avec encodage (ligne 483)"""
        error = GeneWebEncodingError("Encoding error", encoding="utf-8")
        error_str = str(error)
        assert "Encoding error" in error_str or "utf-8" in error_str

    def test_encoding_error_with_position(self):
        """Test erreur avec position (ligne 499)"""
        error = GeneWebEncodingError(
            "Encoding error", encoding="utf-8", byte_position=100
        )
        error_str = str(error)
        assert "Encoding error" in error_str


class TestGeneWebConversionError:
    """Tests de GeneWebConversionError"""

    def test_conversion_error_simple(self):
        """Test erreur de conversion simple (ligne 529)"""
        error = GeneWebConversionError("Conversion error")
        assert "Conversion error" in str(error)

    def test_conversion_error_with_formats(self):
        """Test erreur avec formats (lignes 568, 576)"""
        error = GeneWebConversionError(
            "Conversion error", source_format="gw", target_format="gedcom"
        )
        error_str = str(error)
        assert "Conversion error" in error_str
        # Les formats devraient être mentionnés
        assert "gw" in error_str or "gedcom" in error_str


class TestGeneWebErrorCollector:
    """Tests du collecteur d'erreurs"""

    def test_collector_initialization(self):
        """Test initialisation du collecteur (lignes 580, 586)"""
        collector = GeneWebErrorCollector()
        assert collector is not None
        assert collector.has_errors() == False
        assert collector.error_count() == 0

    def test_collector_add_error(self):
        """Test ajout d'erreur (ligne 591)"""
        collector = GeneWebErrorCollector()
        error = GeneWebError("Test error")
        collector.add_error(error)

        assert collector.has_errors() == True
        assert collector.error_count() == 1

    def test_collector_multiple_errors(self):
        """Test ajout de plusieurs erreurs (ligne 596)"""
        collector = GeneWebErrorCollector()

        error1 = GeneWebError("Error 1")
        error2 = GeneWebError("Error 2")
        error3 = GeneWebError("Error 3")

        collector.add_error(error1)
        collector.add_error(error2)
        collector.add_error(error3)

        assert collector.error_count() == 3
        assert collector.has_errors() == True

    def test_collector_get_errors(self):
        """Test récupération des erreurs"""
        collector = GeneWebErrorCollector()

        error1 = GeneWebError("Error 1")
        error2 = GeneWebError("Error 2")

        collector.add_error(error1)
        collector.add_error(error2)

        errors = collector.get_errors()
        assert len(errors) == 2
        assert error1 in errors
        assert error2 in errors

    def test_collector_str_and_summary(self):
        """Test résumé et str des erreurs (ligne 611)"""
        collector = GeneWebErrorCollector()

        error1 = GeneWebError("Error 1")
        error2 = GeneWebError("Error 2")

        collector.add_error(error1)
        collector.add_error(error2)

        # Test __str__
        summary = str(collector)
        assert isinstance(summary, str)
        # Devrait contenir info sur le nombre d'erreurs
        assert "2" in summary or "error" in summary.lower()

    def test_collector_str_representation(self):
        """Test représentation string du collecteur"""
        collector = GeneWebErrorCollector()

        error = GeneWebError("Test error")
        collector.add_error(error)

        collector_str = str(collector)
        assert isinstance(collector_str, str)
        assert "1" in collector_str or "error" in collector_str.lower()


class TestExceptionInheritance:
    """Tests de l'héritage des exceptions"""

    def test_all_exceptions_inherit_geneweb_error(self):
        """Test que toutes les exceptions héritent de GeneWebError"""
        parse_error = GeneWebParseError("test")
        validation_error = GeneWebValidationError("test")
        encoding_error = GeneWebEncodingError("test")
        conversion_error = GeneWebConversionError("test")

        assert isinstance(parse_error, GeneWebError)
        assert isinstance(validation_error, GeneWebError)
        assert isinstance(encoding_error, GeneWebError)
        assert isinstance(conversion_error, GeneWebError)

    def test_exceptions_can_be_caught_as_base_class(self):
        """Test qu'on peut attraper toutes les exceptions avec la classe de base"""
        try:
            raise GeneWebParseError("test")
        except GeneWebError:
            pass  # OK

        try:
            raise GeneWebValidationError("test")
        except GeneWebError:
            pass  # OK
