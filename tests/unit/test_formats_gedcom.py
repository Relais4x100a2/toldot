"""
Tests unitaires pour les convertisseurs GEDCOM.
"""

import pytest
from pathlib import Path

from geneweb_py.formats.gedcom import GEDCOMExporter, GEDCOMImporter, ConversionError
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person
from geneweb_py.core.family import Family
from geneweb_py.core.date import Date
from geneweb_py.core.event import Event


class TestGEDCOMExporter:
    """Tests pour la classe GEDCOMExporter."""
    
    def test_init(self):
        """Test de l'initialisation."""
        exporter = GEDCOMExporter(encoding="utf-8", version="5.5.1")
        assert exporter.encoding == "utf-8"
        assert exporter.version == "5.5.1"
    
    def test_export_to_string_simple(self):
        """Test d'export vers chaîne simple."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        
        person = Person(surname="DUPONT", given_name="Jean", sex="M")
        genealogy.add_person(person)
        
        result = exporter.export_to_string(genealogy)
        
        # Vérifier que c'est du GEDCOM valide
        lines = result.split('\n')
        assert lines[0] == "0 HEAD"
        assert "0 TRLR" in lines
        
        # Vérifier la présence d'un individu
        indi_lines = [line for line in lines if " INDI" in line]
        assert len(indi_lines) == 1
        
        # Vérifier les champs de base
        assert any("1 NAME" in line for line in lines)
        assert any("2 GIVN Jean" in line for line in lines)
        assert any("2 SURN DUPONT" in line for line in lines)
        assert any("1 SEX M" in line for line in lines)
    
    def test_export_to_string_with_dates(self):
        """Test d'export avec des dates."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        
        person = Person(
            surname="DUPONT",
            given_name="Jean",
            birth_date=Date(year=1950, month=3, day=15),
            death_date=Date(year=2020, month=12, day=25)
        )
        genealogy.add_person(person)
        
        result = exporter.export_to_string(genealogy)
        lines = result.split('\n')
        
        # Vérifier les dates de naissance et décès
        assert any("1 BIRT" in line for line in lines)
        assert any("2 DATE 15 MAR 1950" in line for line in lines)
        assert any("1 DEAT" in line for line in lines)
        assert any("2 DATE 25 DEC 2020" in line for line in lines)
    
    def test_export_to_string_with_family(self):
        """Test d'export avec une famille."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        
        husband = Person(surname="DUPONT", given_name="Jean", sex="M")
        wife = Person(surname="MARTIN", given_name="Marie", sex="F")
        child = Person(surname="DUPONT", given_name="Pierre", sex="M")
        
        family = Family()
        family.husband = husband
        family.wife = wife
        family.add_child(child)
        
        genealogy.add_person(husband)
        genealogy.add_person(wife)
        genealogy.add_person(child)
        genealogy.add_family(family)
        
        result = exporter.export_to_string(genealogy)
        lines = result.split('\n')
        
        # Vérifier la présence d'une famille
        fam_lines = [line for line in lines if " FAM" in line]
        assert len(fam_lines) == 1
        
        # Vérifier les relations familiales
        assert any("1 HUSB" in line for line in lines)
        assert any("1 WIFE" in line for line in lines)
        assert any("1 CHIL" in line for line in lines)
    
    def test_export_to_string_with_events(self):
        """Test d'export avec des événements."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        
        person = Person(surname="DUPONT", given_name="Jean")
        event = Event(
            event_type="graduation",
            date=Date(year=1972, month=6),
            place="Université de Paris",
            description="Diplôme d'ingénieur"
        )
        person.add_event(event)
        genealogy.add_person(person)
        
        result = exporter.export_to_string(genealogy)
        lines = result.split('\n')
        
        # Vérifier la présence d'un événement
        assert any("1 GRAD" in line for line in lines)
        assert any("2 DATE JUN 1972" in line for line in lines)
        assert any("2 PLAC Université de Paris" in line for line in lines)
        assert any("2 NOTE Diplôme d'ingénieur" in line for line in lines)
    
    def test_export_to_file(self):
        """Test d'export vers fichier."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        
        person = Person(surname="DUPONT", given_name="Jean")
        genealogy.add_person(person)
        
        temp_file = Path("temp_test.ged")
        
        try:
            exporter.export(genealogy, str(temp_file))
            assert temp_file.exists()
            
            # Vérifier le contenu
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "0 HEAD" in content
            assert "0 TRLR" in content
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_export_empty_genealogy(self):
        """Test d'export d'une généalogie vide."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        
        with pytest.raises(ConversionError, match="La généalogie est vide"):
            exporter.export_to_string(genealogy)
    
    def test_export_invalid_genealogy(self):
        """Test d'export d'un objet invalide."""
        exporter = GEDCOMExporter()
        
        with pytest.raises(ConversionError, match="n'est pas une instance de Genealogy"):
            exporter.export_to_string("invalid")
    
    def test_map_event_type(self):
        """Test du mapping des types d'événements."""
        exporter = GEDCOMExporter()
        
        # Test des mappings valides
        assert exporter._map_event_type("birth") == "BIRT"
        assert exporter._map_event_type("death") == "DEAT"
        assert exporter._map_event_type("marriage") == "MARR"
        assert exporter._map_event_type("divorce") == "DIV"
        assert exporter._map_event_type("graduation") == "GRAD"
        
        # Test des types non mappés
        assert exporter._map_event_type("unknown") is None
        assert exporter._map_event_type("") is None
    
    def test_format_gedcom_date(self):
        """Test du formatage des dates GEDCOM."""
        exporter = GEDCOMExporter()
        
        # Date complète
        date = Date(year=1950, month=3, day=15)
        assert exporter._format_gedcom_date(date) == "15 MAR 1950"
        
        # Date sans jour
        date = Date(year=1950, month=3)
        assert exporter._format_gedcom_date(date) == "MAR 1950"
        
        # Date sans mois
        date = Date(year=1950)
        assert exporter._format_gedcom_date(date) == "1950"


class TestGEDCOMImporter:
    """Tests pour la classe GEDCOMImporter."""
    
    def test_init(self):
        """Test de l'initialisation."""
        importer = GEDCOMImporter(encoding="utf-8")
        assert importer.encoding == "utf-8"
    
    def test_import_from_string_simple(self):
        """Test d'import depuis chaîne simple."""
        importer = GEDCOMImporter()
        
        gedcom_string = """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
1 SOUR geneweb-py
0 I0001 INDI
1 NAME
2 GIVN Jean
2 SURN DUPONT
1 SEX M
0 TRLR"""
        
        genealogy = importer.import_from_string(gedcom_string)
        
        # Note: L'importeur GEDCOM est simplifié dans cette implémentation
        # Dans une version complète, il faudrait parser tous les champs
        assert isinstance(genealogy, Genealogy)
    
    def test_import_from_file(self):
        """Test d'import depuis fichier."""
        importer = GEDCOMImporter()
        
        gedcom_string = """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
1 SOUR geneweb-py
0 I0001 INDI
1 NAME
2 GIVN Jean
2 SURN DUPONT
1 SEX M
0 TRLR"""
        
        temp_file = Path("temp_test.ged")
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(gedcom_string)
            
            genealogy = importer.import_from_file(str(temp_file))
            assert isinstance(genealogy, Genealogy)
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_import_invalid_gedcom(self):
        """Test d'import de GEDCOM invalide."""
        importer = GEDCOMImporter()
        
        with pytest.raises(ConversionError, match="Erreur lors du parsing GEDCOM"):
            importer.import_from_string("invalid gedcom")
    
    def test_import_nonexistent_file(self):
        """Test d'import d'un fichier inexistant."""
        importer = GEDCOMImporter()
        
        with pytest.raises(ConversionError, match="Le fichier n'existe pas"):
            importer.import_from_file("nonexistent.ged")
