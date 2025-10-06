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
        exporter = BaseExporter()
        assert exporter.encoding == "utf-8"
        
        exporter = BaseExporter(encoding="latin-1")
        assert exporter.encoding == "latin-1"
    
    def test_validate_genealogy_valid(self):
        """Test validation d'une généalogie valide."""
        genealogy = Genealogy()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        genealogy.add_person(person)
        
        exporter = BaseExporter()
        # Ne devrait pas lever d'exception
        exporter._validate_genealogy(genealogy)
    
    def test_validate_genealogy_invalid(self):
        """Test validation d'une généalogie invalide."""
        exporter = BaseExporter()
        
        with pytest.raises(ConversionError):
            exporter._validate_genealogy(None)
        
        with pytest.raises(ConversionError):
            exporter._validate_genealogy("invalid")
    
    def test_abstract_methods(self):
        """Test que les méthodes abstraites ne peuvent pas être appelées."""
        exporter = BaseExporter()
        
        genealogy = Genealogy()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        genealogy.add_person(person)
        
        with pytest.raises(NotImplementedError):
            exporter.export(genealogy, "test.txt")
        
        with pytest.raises(NotImplementedError):
            exporter.export_to_string(genealogy)


class TestBaseImporter:
    """Tests pour BaseImporter."""
    
    def test_base_importer_initialization(self):
        """Test initialisation de BaseImporter."""
        importer = BaseImporter()
        assert importer.encoding == "utf-8"
        
        importer = BaseImporter(encoding="latin-1")
        assert importer.encoding == "latin-1"
    
    def test_abstract_methods(self):
        """Test que les méthodes abstraites ne peuvent pas être appelées."""
        importer = BaseImporter()
        
        with pytest.raises(NotImplementedError):
            importer.import_from_file("test.txt")
        
        with pytest.raises(NotImplementedError):
            importer.import_from_string("test content")
