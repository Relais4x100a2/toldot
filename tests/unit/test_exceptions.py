"""
Tests unitaires pour les exceptions du module geneweb-py

Ces tests vérifient que toutes les exceptions personnalisées
fonctionnent correctement avec leurs messages d'erreur.
"""

import pytest
from geneweb_py.core.exceptions import (
    GeneWebError,
    GeneWebParseError,
    GeneWebValidationError,
    GeneWebConversionError,
    GeneWebEncodingError,
    GeneWebErrorCollector,
    ValidationResult,
)


class TestGeneWebError:
    """Tests pour l'exception de base GeneWebError"""

    def test_basic_error(self):
        """Test création d'une erreur de base"""
        error = GeneWebError("Erreur de test")

        assert str(error) == "Erreur de test"
        assert error.message == "Erreur de test"
        assert error.line_number is None
        assert error.context is None

    def test_error_with_line_number(self):
        """Test erreur avec numéro de ligne"""
        error = GeneWebError("Erreur ligne 5", line_number=5)

        assert str(error) == "Ligne 5: Erreur ligne 5"
        assert error.line_number == 5

    def test_error_with_context(self):
        """Test erreur avec contexte"""
        error = GeneWebError("Erreur de parsing", context="fam CORNO Joseph")

        assert "Erreur de parsing" in str(error)
        assert "fam CORNO Joseph" in str(error)
        assert error.context == "fam CORNO Joseph"

    def test_error_with_line_and_context(self):
        """Test erreur avec ligne et contexte"""
        error = GeneWebError(
            "Erreur de parsing",
            line_number=10,
            context="fam CORNO Joseph + THOMAS Marie",
        )

        assert "Ligne 10" in str(error)
        assert "Erreur de parsing" in str(error)
        assert "fam CORNO Joseph + THOMAS Marie" in str(error)
        assert error.line_number == 10
        assert error.context == "fam CORNO Joseph + THOMAS Marie"

    def test_error_inheritance(self):
        """Test héritage de l'exception"""
        error = GeneWebError("Test héritage")

        assert isinstance(error, Exception)
        assert isinstance(error, GeneWebError)


class TestGeneWebParseError:
    """Tests pour l'exception de parsing"""

    def test_parse_error_basic(self):
        """Test erreur de parsing basique"""
        error = GeneWebParseError("Erreur de parsing", line_number=15)

        assert isinstance(error, GeneWebError)
        assert isinstance(error, GeneWebParseError)
        assert str(error) == "Ligne 15: Erreur de parsing"
        assert error.line_number == 15

    def test_parse_error_with_token(self):
        """Test erreur de parsing avec token"""
        error = GeneWebParseError(
            "Token inattendu",
            line_number=20,
            token="UNKNOWN_TOKEN",
            context="fam CORNO Joseph",
        )

        assert error.token == "UNKNOWN_TOKEN"
        assert error.context == "fam CORNO Joseph"

    def test_parse_error_expected_token(self):
        """Test erreur avec token attendu"""
        error = GeneWebParseError(
            "Token attendu manquant",
            line_number=25,
            expected_token="IDENTIFIER",
            actual_token="EOF",
        )

        assert error.expected_token == "IDENTIFIER"
        assert error.actual_token == "EOF"


class TestGeneWebValidationError:
    """Tests pour l'exception de validation"""

    def test_validation_error_basic(self):
        """Test erreur de validation basique"""
        error = GeneWebValidationError("Données invalides")

        assert isinstance(error, GeneWebError)
        assert isinstance(error, GeneWebValidationError)
        assert str(error) == "Données invalides"

    def test_validation_error_with_field(self):
        """Test erreur de validation avec champ"""
        error = GeneWebValidationError(
            "Valeur invalide", field="birth_date", value="invalid_date"
        )

        assert error.field == "birth_date"
        assert error.value == "invalid_date"

    def test_validation_error_with_entity(self):
        """Test erreur de validation avec entité"""
        error = GeneWebValidationError(
            "Personne invalide", entity_type="Person", entity_id="CORNO_Joseph_0"
        )

        assert error.entity_type == "Person"
        assert error.entity_id == "CORNO_Joseph_0"


class TestGeneWebConversionError:
    """Tests pour l'exception de conversion"""

    def test_conversion_error_basic(self):
        """Test erreur de conversion basique"""
        error = GeneWebConversionError("Erreur de conversion")

        assert isinstance(error, GeneWebError)
        assert isinstance(error, GeneWebConversionError)
        assert str(error) == "Erreur de conversion"

    def test_conversion_error_with_format(self):
        """Test erreur de conversion avec format"""
        error = GeneWebConversionError(
            "Format non supporté", source_format="GeneWeb", target_format="GEDCOM"
        )

        assert error.source_format == "GeneWeb"
        assert error.target_format == "GEDCOM"

    def test_conversion_error_with_data(self):
        """Test erreur de conversion avec données"""
        error = GeneWebConversionError(
            "Données corrompues", data_type="Family", data_value="fam INVALID"
        )

        assert error.data_type == "Family"
        assert error.data_value == "fam INVALID"


class TestGeneWebEncodingError:
    """Tests pour l'exception d'encodage"""

    def test_encoding_error_basic(self):
        """Test erreur d'encodage basique"""
        error = GeneWebEncodingError("Erreur d'encodage")

        assert isinstance(error, GeneWebError)
        assert isinstance(error, GeneWebEncodingError)
        assert str(error) == "Erreur d'encodage"

    def test_encoding_error_with_encoding(self):
        """Test erreur d'encodage avec détails"""
        error = GeneWebEncodingError(
            "Encodage non supporté", encoding="utf-16", detected_encoding="iso-8859-1"
        )

        assert error.encoding == "utf-16"
        assert error.detected_encoding == "iso-8859-1"

    def test_encoding_error_with_byte_position(self):
        """Test erreur d'encodage avec position"""
        error = GeneWebEncodingError(
            "Caractère invalide", byte_position=1024, invalid_byte=b"\xff"
        )

        assert error.byte_position == 1024
        assert error.invalid_byte == b"\xff"


class TestGeneWebErrorCollector:
    """Tests pour le collecteur d'erreurs"""

    def test_error_collector_creation(self):
        """Test création du collecteur"""
        collector = GeneWebErrorCollector()

        assert len(collector.errors) == 0
        assert not collector.has_errors()
        assert len(collector.get_errors()) == 0

    def test_add_single_error(self):
        """Test ajout d'une erreur"""
        collector = GeneWebErrorCollector()
        error = GeneWebParseError("Erreur de test", line_number=10)

        collector.add_error(error)

        assert len(collector.errors) == 1
        assert collector.has_errors()
        assert collector.errors[0] == error

    def test_add_multiple_errors(self):
        """Test ajout de plusieurs erreurs"""
        collector = GeneWebErrorCollector()

        error1 = GeneWebParseError("Erreur 1", line_number=10)
        error2 = GeneWebValidationError("Erreur 2")
        error3 = GeneWebConversionError("Erreur 3")

        collector.add_error(error1)
        collector.add_error(error2)
        collector.add_error(error3)

        assert len(collector.errors) == 3
        assert collector.has_errors()

        errors = collector.get_errors()
        assert len(errors) == 3
        assert errors[0] == error1
        assert errors[1] == error2
        assert errors[2] == error3

    def test_get_errors_by_type(self):
        """Test récupération d'erreurs par type"""
        collector = GeneWebErrorCollector()

        parse_error = GeneWebParseError("Erreur de parsing")
        validation_error1 = GeneWebValidationError("Erreur de validation 1")
        validation_error2 = GeneWebValidationError("Erreur de validation 2")
        conversion_error = GeneWebConversionError("Erreur de conversion")

        collector.add_error(parse_error)
        collector.add_error(validation_error1)
        collector.add_error(validation_error2)
        collector.add_error(conversion_error)

        # Récupérer toutes les erreurs
        all_errors = collector.get_errors()
        assert len(all_errors) == 4

        # Récupérer les erreurs de validation
        validation_errors = collector.get_errors(GeneWebValidationError)
        assert len(validation_errors) == 2
        assert validation_errors[0] == validation_error1
        assert validation_errors[1] == validation_error2

        # Récupérer les erreurs de parsing
        parse_errors = collector.get_errors(GeneWebParseError)
        assert len(parse_errors) == 1
        assert parse_errors[0] == parse_error

    def test_clear_errors(self):
        """Test suppression des erreurs"""
        collector = GeneWebErrorCollector()

        error1 = GeneWebParseError("Erreur 1")
        error2 = GeneWebValidationError("Erreur 2")

        collector.add_error(error1)
        collector.add_error(error2)

        assert len(collector.errors) == 2
        assert collector.has_errors()

        collector.clear_errors()

        assert len(collector.errors) == 0
        assert not collector.has_errors()

    def test_error_count(self):
        """Test comptage des erreurs"""
        collector = GeneWebErrorCollector()

        assert collector.error_count() == 0

        collector.add_error(GeneWebParseError("Erreur 1"))
        assert collector.error_count() == 1

        collector.add_error(GeneWebValidationError("Erreur 2"))
        assert collector.error_count() == 2

        collector.clear_errors()
        assert collector.error_count() == 0

    def test_get_error_summary(self):
        """Test résumé des erreurs"""
        collector = GeneWebErrorCollector()

        # Aucune erreur
        summary = collector.get_error_summary()
        assert summary == "Aucune erreur"

        # Une erreur
        collector.add_error(GeneWebParseError("Erreur de parsing", line_number=10))
        summary = collector.get_error_summary()
        assert "1 erreur" in summary

        # Plusieurs erreurs
        collector.add_error(GeneWebValidationError("Erreur de validation"))
        collector.add_error(GeneWebConversionError("Erreur de conversion"))

        summary = collector.get_error_summary()
        assert "3 erreur" in summary

    def test_context_manager(self):
        """Test utilisation comme contexte manager"""
        collector = GeneWebErrorCollector()

        with collector:
            collector.add_error(GeneWebParseError("Erreur dans le contexte"))

        assert len(collector.errors) == 1
        assert collector.has_errors()

    def test_str_representation(self):
        """Test représentation string"""
        collector = GeneWebErrorCollector()

        # Sans erreurs
        str_repr = str(collector)
        assert "Aucune erreur" in str_repr

        # Avec erreurs
        collector.add_error(GeneWebParseError("Erreur de test", line_number=5))
        str_repr = str(collector)
        assert "1 erreur" in str_repr


class TestValidationResult:
    """Tests pour le résultat de validation"""

    def test_validation_result_success(self):
        """Test résultat de validation réussi"""
        result = ValidationResult()

        assert result.is_valid()
        assert not result.has_errors()
        assert len(result.errors) == 0

    def test_validation_result_with_errors(self):
        """Test résultat de validation avec erreurs"""
        result = ValidationResult()

        error1 = GeneWebValidationError("Erreur 1")
        error2 = GeneWebValidationError("Erreur 2")

        result.add_error(error1)
        result.add_error(error2)

        assert not result.is_valid()
        assert result.has_errors()
        assert len(result.errors) == 2

    def test_validation_result_get_error_messages(self):
        """Test récupération des messages d'erreur"""
        result = ValidationResult()

        error1 = GeneWebValidationError("Première erreur")
        error2 = GeneWebValidationError("Deuxième erreur")

        result.add_error(error1)
        result.add_error(error2)

        messages = result.get_error_messages()
        assert len(messages) == 2
        assert "Première erreur" in messages
        assert "Deuxième erreur" in messages

    def test_validation_result_combined_error(self):
        """Test combinaison avec GeneWebErrorCollector"""
        collector = GeneWebErrorCollector()
        result = ValidationResult()

        # Ajouter des erreurs au collecteur
        collector.add_error(GeneWebParseError("Erreur de parsing"))
        collector.add_error(GeneWebValidationError("Erreur de validation"))

        # Ajouter au résultat
        result.add_errors_from_collector(collector)

        assert not result.is_valid()
        assert result.has_errors()
        assert len(result.errors) == 2

    def test_validation_result_str_representation(self):
        """Test représentation string"""
        result = ValidationResult()

        # Résultat valide
        str_repr = str(result)
        assert "Validation réussie" in str_repr or "Valid" in str_repr

        # Résultat avec erreurs
        result.add_error(GeneWebValidationError("Erreur de test"))
        str_repr = str(result)
        assert "erreur" in str_repr.lower()


class TestExceptionChaining:
    """Tests pour l'enchaînement des exceptions"""

    def test_exception_with_cause(self):
        """Test exception avec cause"""
        try:
            # Simuler une erreur de base
            raise ValueError("Erreur de base")
        except ValueError as e:
            # Créer une exception GeneWeb avec cause
            gw_error = GeneWebParseError("Erreur de parsing", cause=e)

            assert gw_error.cause == e
            assert isinstance(gw_error.cause, ValueError)

    def test_exception_with_multiple_causes(self):
        """Test exception avec plusieurs causes"""
        causes = [
            ValueError("Erreur 1"),
            TypeError("Erreur 2"),
            RuntimeError("Erreur 3"),
        ]

        error = GeneWebConversionError("Erreur de conversion", causes=causes)

        assert len(error.causes) == 3
        assert error.causes[0].args[0] == "Erreur 1"
        assert error.causes[1].args[0] == "Erreur 2"
        assert error.causes[2].args[0] == "Erreur 3"


class TestExceptionMessages:
    """Tests pour les messages d'erreur détaillés"""

    def test_parse_error_detailed_message(self):
        """Test message détaillé d'erreur de parsing"""
        error = GeneWebParseError(
            "Token inattendu",
            line_number=15,
            column=8,
            context="fam CORNO Joseph + THOMAS",
            expected_token="IDENTIFIER",
            actual_token="PLUS",
        )

        message = str(error)
        assert "Token inattendu" in message
        # Le message peut inclure des détails supplémentaires selon l'implémentation

    def test_validation_error_detailed_message(self):
        """Test message détaillé d'erreur de validation"""
        error = GeneWebValidationError(
            "Date de naissance invalide",
            field="birth_date",
            value="32/13/2020",
            entity_type="Person",
            entity_id="CORNO_Joseph_0",
        )

        message = str(error)
        assert "Date de naissance invalide" in message

    def test_conversion_error_detailed_message(self):
        """Test message détaillé d'erreur de conversion"""
        error = GeneWebConversionError(
            "Impossible de convertir la famille",
            source_format="GeneWeb",
            target_format="GEDCOM",
            data_type="Family",
            data_value="fam INVALID_DATA",
        )

        message = str(error)
        assert "Impossible de convertir la famille" in message
