"""
Tests pour améliorer la couverture du module exceptions
"""

import pytest
from geneweb_py.core.exceptions import (
    GeneWebError,
    GeneWebParseError,
    GeneWebValidationError,
    GeneWebEncodingError,
    GeneWebConversionError,
)
from geneweb_py.formats.base import ConversionError


class TestGeneWebErrorCoverage:
    """Tests pour améliorer la couverture de GeneWebError"""

    def test_gene_web_error_basic(self):
        """Test création d'une erreur de base"""
        error = GeneWebError("Message d'erreur")
        assert error.message == "Message d'erreur"
        assert error.line_number is None
        assert error.context is None
        assert str(error) == "Message d'erreur"

    def test_gene_web_error_with_line_number(self):
        """Test création d'une erreur avec numéro de ligne"""
        error = GeneWebError("Message d'erreur", line_number=42)
        assert error.message == "Message d'erreur"
        assert error.line_number == 42
        assert str(error) == "Ligne 42: Message d'erreur"

    def test_gene_web_error_with_context(self):
        """Test création d'une erreur avec contexte"""
        error = GeneWebError("Message d'erreur", context="Contexte d'erreur")
        assert error.message == "Message d'erreur"
        assert error.context == "Contexte d'erreur"
        assert "Message d'erreur" in str(error)
        assert "Contexte d'erreur" in str(error)

    def test_gene_web_error_with_line_and_context(self):
        """Test création d'une erreur avec ligne et contexte"""
        error = GeneWebError("Message d'erreur", line_number=42, context="Contexte")
        assert error.message == "Message d'erreur"
        assert error.line_number == 42
        assert error.context == "Contexte"
        assert "Ligne 42" in str(error)
        assert "Message d'erreur" in str(error)
        assert "Contexte" in str(error)

    def test_gene_web_error_with_kwargs(self):
        """Test création d'une erreur avec arguments supplémentaires"""
        error = GeneWebError("Message d'erreur", custom_attr="valeur")
        assert error.message == "Message d'erreur"
        assert hasattr(error, "custom_attr")
        assert error.custom_attr == "valeur"


class TestGeneWebParseErrorCoverage:
    """Tests pour améliorer la couverture de GeneWebParseError"""

    def test_gene_web_parse_error_basic(self):
        """Test création d'une erreur de parsing de base"""
        error = GeneWebParseError("Erreur de parsing")
        assert error.message == "Erreur de parsing"
        assert error.line_number is None
        assert error.token is None
        assert error.expected is None
        assert str(error) == "Erreur de parsing"

    def test_gene_web_parse_error_with_line_number(self):
        """Test création d'une erreur de parsing avec numéro de ligne"""
        error = GeneWebParseError("Erreur de parsing", line_number=10)
        assert error.message == "Erreur de parsing"
        assert error.line_number == 10
        assert str(error) == "Ligne 10: Erreur de parsing"

    def test_gene_web_parse_error_with_token(self):
        """Test création d'une erreur de parsing avec token"""
        error = GeneWebParseError("Erreur de parsing", token="invalid_token")
        assert error.message == "Erreur de parsing"
        assert error.token == "invalid_token"
        assert "Erreur de parsing" in str(error)
        assert "invalid_token" in str(error)

    def test_gene_web_parse_error_with_expected(self):
        """Test création d'une erreur de parsing avec token attendu"""
        error = GeneWebParseError("Erreur de parsing", expected="fam")
        assert error.message == "Erreur de parsing"
        assert error.expected == "fam"
        assert "Erreur de parsing" in str(error)
        assert "fam" in str(error)

    def test_gene_web_parse_error_with_all_params(self):
        """Test création d'une erreur de parsing avec tous les paramètres"""
        error = GeneWebParseError(
            "Erreur de parsing",
            line_number=15,
            token="invalid",
            expected="fam",
            context="Dans un bloc famille",
        )
        assert error.message == "Erreur de parsing"
        assert error.line_number == 15
        assert error.token == "invalid"
        assert error.expected == "fam"
        assert error.context == "Dans un bloc famille"
        error_str = str(error)
        assert "Ligne 15" in error_str
        assert "Erreur de parsing" in error_str
        assert "invalid" in error_str
        assert "fam" in error_str
        assert "Dans un bloc famille" in error_str

    def test_gene_web_parse_error_with_kwargs(self):
        """Test création d'une erreur de parsing avec arguments supplémentaires"""
        error = GeneWebParseError("Erreur de parsing", custom_attr="valeur")
        assert error.message == "Erreur de parsing"
        assert hasattr(error, "custom_attr")
        assert error.custom_attr == "valeur"


class TestGeneWebValidationErrorCoverage:
    """Tests pour améliorer la couverture de GeneWebValidationError"""

    def test_gene_web_validation_error_basic(self):
        """Test création d'une erreur de validation de base"""
        error = GeneWebValidationError("Erreur de validation")
        assert error.message == "Erreur de validation"
        assert error.line_number is None
        assert error.field is None
        assert error.value is None
        assert str(error) == "Erreur de validation"

    def test_gene_web_validation_error_with_line_number(self):
        """Test création d'une erreur de validation avec numéro de ligne"""
        error = GeneWebValidationError("Erreur de validation", line_number=20)
        assert error.message == "Erreur de validation"
        assert error.line_number == 20
        assert str(error) == "Ligne 20: Erreur de validation"

    def test_gene_web_validation_error_with_field(self):
        """Test création d'une erreur de validation avec champ"""
        error = GeneWebValidationError("Erreur de validation", field="nom")
        assert error.message == "Erreur de validation"
        assert error.field == "nom"
        assert "Erreur de validation" in str(error)
        assert "nom" in str(error)

    def test_gene_web_validation_error_with_value(self):
        """Test création d'une erreur de validation avec valeur"""
        error = GeneWebValidationError("Erreur de validation", value="valeur_invalide")
        assert error.message == "Erreur de validation"
        assert error.value == "valeur_invalide"
        assert "Erreur de validation" in str(error)
        assert "valeur_invalide" in str(error)

    def test_gene_web_validation_error_with_all_params(self):
        """Test création d'une erreur de validation avec tous les paramètres"""
        error = GeneWebValidationError(
            "Erreur de validation",
            line_number=25,
            field="nom",
            value="valeur_invalide",
            context="Validation d'une personne",
        )
        assert error.message == "Erreur de validation"
        assert error.line_number == 25
        assert error.field == "nom"
        assert error.value == "valeur_invalide"
        assert error.context == "Validation d'une personne"
        error_str = str(error)
        assert "Ligne 25" in error_str
        assert "Erreur de validation" in error_str
        assert "nom" in error_str
        assert "valeur_invalide" in error_str
        assert "Validation d'une personne" in error_str

    def test_gene_web_validation_error_with_kwargs(self):
        """Test création d'une erreur de validation avec arguments supplémentaires"""
        error = GeneWebValidationError("Erreur de validation", custom_attr="valeur")
        assert error.message == "Erreur de validation"
        assert hasattr(error, "custom_attr")
        assert error.custom_attr == "valeur"


class TestGeneWebEncodingErrorCoverage:
    """Tests pour améliorer la couverture de GeneWebEncodingError"""

    def test_gene_web_encoding_error_basic(self):
        """Test création d'une erreur d'encodage de base"""
        error = GeneWebEncodingError("Erreur d'encodage")
        assert error.message == "Erreur d'encodage"
        assert error.line_number is None
        assert error.encoding is None
        assert str(error) == "Erreur d'encodage"

    def test_gene_web_encoding_error_with_line_number(self):
        """Test création d'une erreur d'encodage avec numéro de ligne"""
        error = GeneWebEncodingError("Erreur d'encodage", line_number=30)
        assert error.message == "Erreur d'encodage"
        assert error.line_number == 30
        assert str(error) == "Ligne 30: Erreur d'encodage"

    def test_gene_web_encoding_error_with_encoding(self):
        """Test création d'une erreur d'encodage avec encodage"""
        error = GeneWebEncodingError("Erreur d'encodage", encoding="utf-8")
        assert error.message == "Erreur d'encodage"
        assert error.encoding == "utf-8"
        assert str(error) == "Erreur d'encodage"

    def test_gene_web_encoding_error_with_all_params(self):
        """Test création d'une erreur d'encodage avec tous les paramètres"""
        error = GeneWebEncodingError(
            "Erreur d'encodage",
            line_number=35,
            encoding="iso-8859-1",
            context="Lecture du fichier",
        )
        assert error.message == "Erreur d'encodage"
        assert error.line_number == 35
        assert error.encoding == "iso-8859-1"
        assert error.context == "Lecture du fichier"
        error_str = str(error)
        assert "Ligne 35" in error_str
        assert "Erreur d'encodage" in error_str
        assert "Lecture du fichier" in error_str

    def test_gene_web_encoding_error_with_kwargs(self):
        """Test création d'une erreur d'encodage avec arguments supplémentaires"""
        error = GeneWebEncodingError("Erreur d'encodage", custom_attr="valeur")
        assert error.message == "Erreur d'encodage"
        assert hasattr(error, "custom_attr")
        assert error.custom_attr == "valeur"


class TestGeneWebConversionErrorCoverage:
    """Tests pour améliorer la couverture de GeneWebConversionError"""

    def test_gene_web_conversion_error_basic(self):
        """Test création d'une erreur de conversion de base"""
        error = GeneWebConversionError("Erreur de conversion")
        assert error.message == "Erreur de conversion"
        assert error.line_number is None
        assert error.source_format is None
        assert error.target_format is None
        assert str(error) == "Erreur de conversion"

    def test_gene_web_conversion_error_with_line_number(self):
        """Test création d'une erreur de conversion avec numéro de ligne"""
        error = GeneWebConversionError("Erreur de conversion", line_number=40)
        assert error.message == "Erreur de conversion"
        assert error.line_number == 40
        assert str(error) == "Ligne 40: Erreur de conversion"

    def test_gene_web_conversion_error_with_formats(self):
        """Test création d'une erreur de conversion avec formats"""
        error = GeneWebConversionError(
            "Erreur de conversion", source_format="gw", target_format="gedcom"
        )
        assert error.message == "Erreur de conversion"
        assert error.source_format == "gw"
        assert error.target_format == "gedcom"
        error_str = str(error)
        assert "Erreur de conversion" in error_str
        assert "gw" in error_str
        assert "gedcom" in error_str

    def test_gene_web_conversion_error_with_all_params(self):
        """Test création d'une erreur de conversion avec tous les paramètres"""
        error = GeneWebConversionError(
            "Erreur de conversion",
            line_number=45,
            source_format="gw",
            target_format="json",
            context="Conversion vers JSON",
        )
        assert error.message == "Erreur de conversion"
        assert error.line_number == 45
        assert error.source_format == "gw"
        assert error.target_format == "json"
        assert error.context == "Conversion vers JSON"
        error_str = str(error)
        assert "Ligne 45" in error_str
        assert "Erreur de conversion" in error_str
        assert "gw" in error_str
        assert "json" in error_str
        assert "Conversion vers JSON" in error_str

    def test_gene_web_conversion_error_with_kwargs(self):
        """Test création d'une erreur de conversion avec arguments supplémentaires"""
        error = GeneWebConversionError("Erreur de conversion", custom_attr="valeur")
        assert error.message == "Erreur de conversion"
        assert hasattr(error, "custom_attr")
        assert error.custom_attr == "valeur"


class TestConversionErrorCoverage:
    """Tests pour améliorer la couverture de ConversionError"""

    def test_conversion_error_basic(self):
        """Test création d'une ConversionError de base"""
        error = ConversionError("Erreur de conversion")
        assert error.message == "Erreur de conversion"
        assert error.details == {}
        assert str(error) == "Erreur de conversion"

    def test_conversion_error_with_details(self):
        """Test création d'une ConversionError avec détails"""
        details = {"field": "nom", "value": "invalide"}
        error = ConversionError("Erreur de conversion", details=details)
        assert error.message == "Erreur de conversion"
        assert error.details == details
        assert str(error) == "Erreur de conversion"

    def test_conversion_error_with_kwargs(self):
        """Test création d'une ConversionError avec arguments supplémentaires"""
        error = ConversionError(
            "Erreur de conversion", line_number=50, custom_attr="valeur"
        )
        assert error.message == "Erreur de conversion"
        assert error.line_number == 50
        assert hasattr(error, "custom_attr")
        assert error.custom_attr == "valeur"

    def test_conversion_error_inheritance(self):
        """Test que ConversionError hérite bien de GeneWebConversionError"""
        error = ConversionError("Erreur de conversion")
        assert isinstance(error, GeneWebConversionError)
        assert isinstance(error, GeneWebError)


class TestExceptionInheritanceCoverage:
    """Tests pour vérifier l'héritage des exceptions"""

    def test_gene_web_parse_error_inheritance(self):
        """Test que GeneWebParseError hérite bien de GeneWebError"""
        error = GeneWebParseError("Erreur de parsing")
        assert isinstance(error, GeneWebError)
        assert isinstance(error, Exception)

    def test_gene_web_validation_error_inheritance(self):
        """Test que GeneWebValidationError hérite bien de GeneWebError"""
        error = GeneWebValidationError("Erreur de validation")
        assert isinstance(error, GeneWebError)
        assert isinstance(error, Exception)

    def test_gene_web_encoding_error_inheritance(self):
        """Test que GeneWebEncodingError hérite bien de GeneWebError"""
        error = GeneWebEncodingError("Erreur d'encodage")
        assert isinstance(error, GeneWebError)
        assert isinstance(error, Exception)

    def test_gene_web_conversion_error_inheritance(self):
        """Test que GeneWebConversionError hérite bien de GeneWebError"""
        error = GeneWebConversionError("Erreur de conversion")
        assert isinstance(error, GeneWebError)
        assert isinstance(error, Exception)

    def test_conversion_error_inheritance(self):
        """Test que ConversionError hérite bien de GeneWebConversionError"""
        error = ConversionError("Erreur de conversion")
        assert isinstance(error, GeneWebConversionError)
        assert isinstance(error, GeneWebError)
        assert isinstance(error, Exception)


class TestExceptionMessageFormattingCoverage:
    """Tests pour vérifier le formatage des messages d'erreur"""

    def test_error_message_without_line_number(self):
        """Test formatage du message sans numéro de ligne"""
        error = GeneWebError("Message simple")
        assert str(error) == "Message simple"

    def test_error_message_with_line_number(self):
        """Test formatage du message avec numéro de ligne"""
        error = GeneWebError("Message avec ligne", line_number=123)
        assert str(error) == "Ligne 123: Message avec ligne"

    def test_error_message_with_zero_line_number(self):
        """Test formatage du message avec numéro de ligne zéro"""
        error = GeneWebError("Message ligne zéro", line_number=0)
        assert str(error) == "Ligne 0: Message ligne zéro"

    def test_error_message_with_negative_line_number(self):
        """Test formatage du message avec numéro de ligne négatif"""
        error = GeneWebError("Message ligne négative", line_number=-1)
        assert str(error) == "Ligne -1: Message ligne négative"

    def test_error_message_with_large_line_number(self):
        """Test formatage du message avec grand numéro de ligne"""
        error = GeneWebError("Message grande ligne", line_number=999999)
        assert str(error) == "Ligne 999999: Message grande ligne"

    def test_error_message_with_special_characters(self):
        """Test formatage du message avec caractères spéciaux"""
        error = GeneWebError("Message avec caractères spéciaux: éàçù")
        assert str(error) == "Message avec caractères spéciaux: éàçù"

    def test_error_message_with_newlines(self):
        """Test formatage du message avec retours à la ligne"""
        error = GeneWebError("Message avec\nretours à la ligne")
        assert str(error) == "Message avec\nretours à la ligne"

    def test_error_message_with_tabs(self):
        """Test formatage du message avec tabulations"""
        error = GeneWebError("Message avec\ttabulations")
        assert str(error) == "Message avec\ttabulations"
