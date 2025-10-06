"""
Tests pour les classes de base des convertisseurs
"""

import pytest
from geneweb_py.formats.base import BaseExporter, BaseImporter, ConversionError
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.date import Date


class TestConversionError:
    """Tests pour ConversionError."""
    
    def test_conversion_error_creation(self):
        """Test création d'une ConversionError."""
        error = ConversionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_conversion_error_with_details(self):
        """Test ConversionError avec détails."""
        error = ConversionError("Test error", details={"line": 10, "column": 5})
        assert str(error) == "Test error"
        assert hasattr(error, 'details')


class TestBaseExporter:
    """Tests pour BaseExporter."""
    
    def test_base_exporter_initialization(self):
        """Test initialisation de BaseExporter."""
        class ConcreteExporter(BaseExporter):
            def export(self, genealogy, output_path):
                pass
            def export_to_string(self, genealogy):
                return ""
        
        exporter = ConcreteExporter()
        assert exporter.encoding == "utf-8"
        
        exporter = ConcreteExporter(encoding="latin-1")
        assert exporter.encoding == "latin-1"
    
    def test_validate_genealogy_valid(self):
        """Test validation d'une généalogie valide."""
        class ConcreteExporter(BaseExporter):
            def export(self, genealogy, output_path):
                pass
            def export_to_string(self, genealogy):
                return ""
        
        genealogy = Genealogy()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        genealogy.add_person(person)
        
        exporter = ConcreteExporter()
        # Ne devrait pas lever d'exception
        exporter._validate_genealogy(genealogy)
    
    def test_validate_genealogy_invalid(self):
        """Test validation d'une généalogie invalide."""
        class ConcreteExporter(BaseExporter):
            def export(self, genealogy, output_path):
                pass
            def export_to_string(self, genealogy):
                return ""
        
        exporter = ConcreteExporter()
        
        with pytest.raises(ConversionError):
            exporter._validate_genealogy(None)
        
        with pytest.raises(ConversionError):
            exporter._validate_genealogy("invalid")
    
    def test_abstract_methods(self):
        """Test que les méthodes abstraites ne peuvent pas être appelées."""
        class ConcreteExporter(BaseExporter):
            def export(self, genealogy, output_path):
                pass
            def export_to_string(self, genealogy):
                return ""
        
        exporter = ConcreteExporter()
        
        genealogy = Genealogy()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        genealogy.add_person(person)
        
        # Ces méthodes devraient être implémentées par les sous-classes
        # Mais notre classe concrète les implémente, donc elles ne lèvent pas d'erreur
        exporter.export(genealogy, "test.txt")
        result = exporter.export_to_string(genealogy)
        assert result == ""


class TestBaseImporter:
    """Tests pour BaseImporter."""
    
    def test_base_importer_initialization(self):
        """Test initialisation de BaseImporter."""
        class ConcreteImporter(BaseImporter):
            def import_from_file(self, file_path):
                return Genealogy()
            def import_from_string(self, content):
                return Genealogy()
        
        importer = ConcreteImporter()
        assert importer.encoding == "utf-8"
        
        importer = ConcreteImporter(encoding="latin-1")
        assert importer.encoding == "latin-1"
    
    def test_abstract_methods(self):
        """Test que les méthodes abstraites ne peuvent pas être appelées."""
        class ConcreteImporter(BaseImporter):
            def import_from_file(self, file_path):
                return Genealogy()
            def import_from_string(self, content):
                return Genealogy()
        
        importer = ConcreteImporter()
        
        # Ces méthodes devraient être implémentées par les sous-classes
        # Mais notre classe concrète les implémente, donc elles ne lèvent pas d'erreur
        result1 = importer.import_from_file("test.txt")
        assert isinstance(result1, Genealogy)
        
        result2 = importer.import_from_string("test content")
        assert isinstance(result2, Genealogy)
