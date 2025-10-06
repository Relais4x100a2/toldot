"""
Tests unitaires pour les classes de base des convertisseurs.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from geneweb_py.formats.base import BaseExporter, BaseImporter, ConversionError
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender


class ConcreteExporter(BaseExporter):
    """Implémentation concrète pour les tests."""
    
    def export(self, genealogy: Genealogy, output_path: str) -> None:
        """Export vers un fichier."""
        pass
    
    def export_to_string(self, genealogy: Genealogy) -> str:
        """Export vers une chaîne."""
        return "test"


class ConcreteImporter(BaseImporter):
    """Implémentation concrète pour les tests."""
    
    def import_from_file(self, file_path: str) -> Genealogy:
        """Import depuis un fichier."""
        return Genealogy()
    
    def import_from_string(self, content: str) -> Genealogy:
        """Import depuis une chaîne."""
        return Genealogy()


class TestBaseExporter:
    """Tests pour la classe BaseExporter."""
    
    def test_init(self):
        """Test de l'initialisation."""
        exporter = ConcreteExporter(encoding="utf-8")
        assert exporter.encoding == "utf-8"
    
    def test_validate_genealogy_valid(self):
        """Test de validation d'une généalogie valide."""
        exporter = ConcreteExporter()
        genealogy = Genealogy()
        genealogy.add_person(Person(last_name="TEST", first_name="Test"))
        
        # Ne doit pas lever d'exception
        exporter._validate_genealogy(genealogy)
    
    def test_validate_genealogy_invalid_type(self):
        """Test de validation d'un objet invalide."""
        exporter = ConcreteExporter()
        
        with pytest.raises(ConversionError, match="n'est pas une instance de Genealogy"):
            exporter._validate_genealogy("invalid")
    
    def test_validate_genealogy_empty(self):
        """Test de validation d'une généalogie vide."""
        exporter = ConcreteExporter()
        genealogy = Genealogy()
        
        with pytest.raises(ConversionError, match="La généalogie est vide"):
            exporter._validate_genealogy(genealogy)


class TestBaseImporter:
    """Tests pour la classe BaseImporter."""
    
    def test_init(self):
        """Test de l'initialisation."""
        importer = ConcreteImporter(encoding="utf-8")
        assert importer.encoding == "utf-8"
    
    def test_validate_file_path_valid(self):
        """Test de validation d'un chemin de fichier valide."""
        importer = ConcreteImporter()
        
        # Créer un fichier temporaire
        temp_file = Path("temp_test_file.txt")
        temp_file.write_text("test content")
        
        try:
            result = importer._validate_file_path(temp_file)
            assert result == temp_file
        finally:
            temp_file.unlink()
    
    def test_validate_file_path_nonexistent(self):
        """Test de validation d'un fichier inexistant."""
        importer = ConcreteImporter()
        
        with pytest.raises(ConversionError, match="Le fichier n'existe pas"):
            importer._validate_file_path("nonexistent_file.txt")
    
    def test_validate_file_path_not_file(self):
        """Test de validation d'un répertoire."""
        importer = ConcreteImporter()
        
        with pytest.raises(ConversionError, match="n'est pas un fichier"):
            importer._validate_file_path(Path("."))


class TestConversionError:
    """Tests pour la classe ConversionError."""
    
    def test_inheritance(self):
        """Test que ConversionError hérite de GeneWebConversionError."""
        from geneweb_py.core.exceptions import GeneWebConversionError
        
        error = ConversionError("test message")
        assert isinstance(error, GeneWebConversionError)
    
    def test_message(self):
        """Test du message d'erreur."""
        message = "Test error message"
        error = ConversionError(message)
        assert str(error) == message
