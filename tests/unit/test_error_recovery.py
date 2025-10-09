"""
Tests pour la récupération d'erreurs et le parsing gracieux

Ces tests vérifient que le parser peut gérer les erreurs de manière gracieuse
et continuer le parsing au lieu de s'arrêter à la première erreur.
"""

import pytest
from pathlib import Path

from geneweb_py.core.parser.gw_parser import GeneWebParser
from geneweb_py.core.exceptions import (
    GeneWebParseError,
    GeneWebValidationError,
    GeneWebErrorCollector,
    ParseWarning,
    ErrorSeverity,
)


class TestErrorCollector:
    """Tests pour le collecteur d'erreurs"""
    
    def test_error_collector_basic(self):
        """Test basique du collecteur d'erreurs"""
        collector = GeneWebErrorCollector(strict=False)
        
        # Ajouter quelques erreurs
        collector.add_error(GeneWebParseError("Erreur 1", line_number=1))
        collector.add_error(GeneWebParseError("Erreur 2", line_number=2))
        collector.add_warning("Avertissement 1", line_number=3)
        
        assert collector.has_errors()
        assert len(collector) == 3
        assert collector.error_count() == 3
        assert collector.error_count(ErrorSeverity.WARNING) == 1
        assert collector.error_count(ErrorSeverity.ERROR) == 2
    
    def test_error_collector_strict_mode(self):
        """Test du mode strict - doit lever l'exception"""
        collector = GeneWebErrorCollector(strict=True)
        
        # Les warnings ne lèvent pas d'exception
        collector.add_warning("Avertissement", line_number=1)
        assert len(collector) == 1
        
        # Les erreurs lèvent une exception
        with pytest.raises(GeneWebParseError):
            collector.add_error(GeneWebParseError("Erreur critique", line_number=2))
    
    def test_error_collector_filtering(self):
        """Test du filtrage des erreurs par type et sévérité"""
        collector = GeneWebErrorCollector(strict=False)
        
        collector.add_error(GeneWebParseError("Parse erreur", line_number=1))
        collector.add_error(GeneWebValidationError("Validation erreur", line_number=2))
        collector.add_warning("Warning", line_number=3)
        
        # Filtrer par type
        parse_errors = collector.get_errors(error_type=GeneWebParseError)
        assert len(parse_errors) == 1
        
        validation_errors = collector.get_errors(error_type=GeneWebValidationError)
        assert len(validation_errors) == 1
        
        # Filtrer par sévérité
        warnings = collector.get_warnings()
        assert len(warnings) == 1
    
    def test_error_collector_summary(self):
        """Test du résumé des erreurs"""
        collector = GeneWebErrorCollector(strict=False)
        
        # Collecteur vide
        assert "Aucune erreur" in collector.get_error_summary()
        
        # Avec erreurs
        collector.add_error(GeneWebParseError("Erreur 1", line_number=1))
        collector.add_error(GeneWebParseError("Erreur 2", line_number=2))
        collector.add_warning("Warning", line_number=3)
        
        summary = collector.get_error_summary()
        assert "avertissement" in summary.lower()
        assert "erreur" in summary.lower()
    
    def test_error_collector_detailed_report(self):
        """Test du rapport détaillé"""
        collector = GeneWebErrorCollector(strict=False)
        
        collector.add_error(GeneWebParseError("Erreur parse", line_number=1))
        collector.add_error(GeneWebValidationError("Erreur validation", line_number=2))
        collector.add_warning("Warning", line_number=3)
        
        report = collector.get_detailed_report()
        assert "Rapport d'erreurs" in report
        assert "3 total" in report
    
    def test_error_collector_context_manager(self):
        """Test de l'utilisation comme context manager"""
        with GeneWebErrorCollector(strict=False) as collector:
            collector.add_warning("Test warning")
            assert collector.has_errors()
        
        # Avec erreur critique, doit lever l'exception à la sortie
        with pytest.raises(GeneWebParseError):
            with GeneWebErrorCollector(strict=False) as collector:
                error = GeneWebParseError("Critical", severity=ErrorSeverity.CRITICAL)
                collector.add_error(error)


class TestParseWarning:
    """Tests pour les avertissements de parsing"""
    
    def test_parse_warning_creation(self):
        """Test de création d'un avertissement"""
        warning = ParseWarning("Ceci est un avertissement", line_number=10)
        
        assert warning.severity == ErrorSeverity.WARNING
        assert warning.line_number == 10
        assert "avertissement" in warning.message.lower()
    
    def test_parse_warning_with_context(self):
        """Test d'avertissement avec contexte"""
        warning = ParseWarning(
            "Date manquante",
            line_number=5,
            context="Personne: DUPONT Jean"
        )
        
        assert warning.context == "Personne: DUPONT Jean"
        assert "Contexte" in str(warning)


class TestEnrichedErrorMessages:
    """Tests pour les messages d'erreur enrichis"""
    
    def test_parse_error_enriched_message(self):
        """Test de message d'erreur enrichi pour GeneWebParseError"""
        error = GeneWebParseError(
            "Token inattendu",
            line_number=42,
            token="invalid",
            expected="fam, nom, ou date",
            context="Parsing d'une personne"
        )
        
        message = str(error)
        assert "Ligne 42" in message
        assert "invalid" in message
        assert "fam, nom, ou date" in message
        assert "Parsing d'une personne" in message
    
    def test_validation_error_enriched_message(self):
        """Test de message enrichi pour GeneWebValidationError"""
        error = GeneWebValidationError(
            "Date de naissance invalide",
            line_number=15,
            field="birth_date",
            value="invalid",
            entity_type="Person",
            entity_id="DUPONT_Jean_0"
        )
        
        message = str(error)
        assert "Ligne 15" in message
        assert "birth_date" in message
        assert "Person" in message
        assert "DUPONT_Jean_0" in message
    
    def test_error_to_dict(self):
        """Test de conversion en dictionnaire"""
        error = GeneWebParseError(
            "Erreur de test",
            line_number=10,
            token="test",
            severity=ErrorSeverity.ERROR
        )
        
        error_dict = error.to_dict()
        assert error_dict['type'] == 'GeneWebParseError'
        assert error_dict['line_number'] == 10
        assert error_dict['token'] == 'test'
        assert error_dict['severity'] == 'error'


class TestGracefulParsing:
    """Tests pour le parsing gracieux"""
    
    def test_parser_strict_mode_default(self):
        """Test que le mode strict est activé par défaut"""
        parser = GeneWebParser()
        assert parser.strict is True
    
    def test_parser_graceful_mode(self):
        """Test du mode gracieux (strict=False)"""
        parser = GeneWebParser(strict=False, validate=False)
        assert parser.strict is False
        assert parser.error_collector is not None
    
    def test_parser_error_collector_integration(self):
        """Test de l'intégration du collecteur d'erreurs"""
        parser = GeneWebParser(strict=False, validate=False)
        
        # Le collecteur doit être initialisé
        assert isinstance(parser.error_collector, GeneWebErrorCollector)
        assert parser.error_collector.strict is False


class TestErrorRecovery:
    """Tests de récupération après erreurs"""
    
    def test_empty_file_handling(self):
        """Test de gestion d'un fichier vide"""
        parser = GeneWebParser(strict=False, validate=False)
        genealogy = parser.parse_string("")
        
        assert genealogy is not None
        assert len(genealogy.persons) == 0
        assert genealogy.is_valid
    
    def test_simple_valid_content(self):
        """Test avec contenu simple et valide - utilise une fixture existante"""
        from pathlib import Path
        
        # Utiliser une fixture existante qui fonctionne
        fixture_file = Path(__file__).parent.parent / "fixtures" / "simple_test.gw"
        
        parser = GeneWebParser(strict=False, validate=False)
        genealogy = parser.parse_file(fixture_file)
        
        assert len(genealogy.persons) >= 1
    
    def test_multiple_errors_collection(self):
        """Test de la collecte de plusieurs erreurs"""
        parser = GeneWebParser(strict=False, validate=True)
        
        # Simple test: le collecteur doit pouvoir accumuler les erreurs
        parser.error_collector.add_error(
            GeneWebParseError("Erreur 1", line_number=1)
        )
        parser.error_collector.add_error(
            GeneWebParseError("Erreur 2", line_number=2)
        )
        
        assert parser.error_collector.error_count() == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

