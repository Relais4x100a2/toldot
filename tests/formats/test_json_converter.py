"""
Tests pour le convertisseur JSON
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from geneweb_py.formats.json import JSONExporter, JSONImporter, ConversionError
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.family import Family, MarriageStatus
from geneweb_py.core.event import Event, EventType
from geneweb_py.core.date import Date


@pytest.fixture
def sample_genealogy():
    """Généalogie de test pour les tests."""
    genealogy = Genealogy()
    
    # Ajouter des personnes
    person1 = Person(
        last_name="DUPONT",
        first_name="Jean",
        gender=Gender.MALE,
        birth_date=Date(day=15, month=6, year=1990),
        birth_place="Paris"
    )
    genealogy.add_person(person1)
    
    person2 = Person(
        last_name="MARTIN",
        first_name="Marie",
        gender=Gender.FEMALE,
        birth_date=Date(day=20, month=8, year=1992),
        birth_place="Lyon"
    )
    genealogy.add_person(person2)
    
    # Ajouter une famille
    family = Family(
        family_id="family_1",
        husband_id=person1.unique_id,
        wife_id=person2.unique_id,
        marriage_status=MarriageStatus.MARRIED,
        marriage_date=Date(day=10, month=5, year=2015),
        marriage_place="Marseille"
    )
    genealogy.add_family(family)
    
    return genealogy


class TestJSONExporter:
    """Tests pour JSONExporter."""
    
    def test_export_to_file(self, sample_genealogy):
        """Test export vers un fichier JSON."""
        exporter = JSONExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            exporter.export(sample_genealogy, temp_path)
            
            # Vérifier que le fichier a été créé
            assert os.path.exists(temp_path)
            
            # Vérifier le contenu JSON
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert "genealogy" in data
            assert "persons" in data["genealogy"]
            assert "families" in data["genealogy"]
            assert len(data["genealogy"]["persons"]) == 2
            assert len(data["genealogy"]["families"]) == 1
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_string(self, sample_genealogy):
        """Test export vers une chaîne JSON."""
        exporter = JSONExporter()
        
        json_string = exporter.export_to_string(sample_genealogy)
        
        # Vérifier que c'est du JSON valide
        data = json.loads(json_string)
        assert "genealogy" in data
        assert "persons" in data["genealogy"]
        assert "families" in data["genealogy"]
    
    def test_export_with_custom_settings(self, sample_genealogy):
        """Test export avec paramètres personnalisés."""
        exporter = JSONExporter(indent=4, ensure_ascii=True)
        
        json_string = exporter.export_to_string(sample_genealogy)
        
        # Vérifier que c'est du JSON valide
        data = json.loads(json_string)
        assert "genealogy" in data
    
    def test_export_invalid_genealogy(self):
        """Test export avec généalogie invalide."""
        exporter = JSONExporter()
        
        with pytest.raises(ConversionError):
            exporter.export(None, "test.json")
    
    def test_export_to_invalid_path(self, sample_genealogy):
        """Test export vers chemin invalide."""
        exporter = JSONExporter()
        
        with pytest.raises(ConversionError):
            exporter.export(sample_genealogy, "/invalid/path/test.json")


class TestJSONImporter:
    """Tests pour JSONImporter."""
    
    def test_import_from_file(self, sample_genealogy):
        """Test import depuis un fichier JSON."""
        # D'abord exporter vers un fichier
        exporter = JSONExporter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            exporter.export(sample_genealogy, temp_path)
            
            # Maintenant importer
            importer = JSONImporter()
            imported_genealogy = importer.import_from_file(temp_path)
            
            # Vérifier que la généalogie a été importée
            assert imported_genealogy is not None
            assert len(imported_genealogy.persons) == 2
            assert len(imported_genealogy.families) == 1
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_import_from_string(self, sample_genealogy):
        """Test import depuis une chaîne JSON."""
        # D'abord exporter vers une chaîne
        exporter = JSONExporter()
        json_string = exporter.export_to_string(sample_genealogy)
        
        # Maintenant importer
        importer = JSONImporter()
        imported_genealogy = importer.import_from_string(json_string)
        
        # Vérifier que la généalogie a été importée
        assert imported_genealogy is not None
        assert len(imported_genealogy.persons) == 2
        assert len(imported_genealogy.families) == 1
    
    def test_import_invalid_json(self):
        """Test import avec JSON invalide."""
        importer = JSONImporter()
        
        with pytest.raises(ConversionError):
            importer.import_from_string("invalid json")
    
    def test_import_from_nonexistent_file(self):
        """Test import depuis fichier inexistant."""
        importer = JSONImporter()
        
        with pytest.raises(ConversionError):
            importer.import_from_file("nonexistent.json")
    
    def test_import_empty_json(self):
        """Test import avec JSON vide."""
        importer = JSONImporter()
        
        with pytest.raises(ConversionError):
            importer.import_from_string("{}")


class TestJSONConverterIntegration:
    """Tests d'intégration pour le convertisseur JSON."""
    
    def test_round_trip_conversion(self, sample_genealogy):
        """Test conversion aller-retour (export puis import)."""
        exporter = JSONExporter()
        importer = JSONImporter()
        
        # Export
        json_string = exporter.export_to_string(sample_genealogy)
        
        # Import
        imported_genealogy = importer.import_from_string(json_string)
        
        # Vérifier que les données sont identiques
        assert len(imported_genealogy.persons) == len(sample_genealogy.persons)
        assert len(imported_genealogy.families) == len(sample_genealogy.families)
        
        # Vérifier les détails des personnes
        original_persons = list(sample_genealogy.persons.values())
        imported_persons = list(imported_genealogy.persons.values())
        
        assert original_persons[0].last_name == imported_persons[0].last_name
        assert original_persons[0].first_name == imported_persons[0].first_name
        assert original_persons[0].gender == imported_persons[0].gender
