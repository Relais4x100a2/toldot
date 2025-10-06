"""
Tests unitaires pour les convertisseurs XML.
"""

import pytest
from pathlib import Path
import xml.etree.ElementTree as ET

from geneweb_py.formats.xml import XMLExporter, XMLImporter, ConversionError
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.family import Family
from geneweb_py.core.date import Date
from geneweb_py.core.event import Event, EventType


class TestXMLExporter:
    """Tests pour la classe XMLExporter."""
    
    def test_init(self):
        """Test de l'initialisation."""
        exporter = XMLExporter(encoding="utf-8", pretty_print=True)
        assert exporter.encoding == "utf-8"
        assert exporter.pretty_print is True
    
    def test_export_to_string_simple(self):
        """Test d'export vers chaîne simple."""
        exporter = XMLExporter()
        genealogy = Genealogy()
        
        person = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        genealogy.add_person(person)
        
        result = exporter.export_to_string(genealogy)
        
        # Vérifier que c'est du XML valide
        root = ET.fromstring(result)
        assert root.tag == "genealogy"
        assert root.get("version") == "1.0.0"
        
        persons_elem = root.find("persons")
        assert persons_elem is not None
        assert len(persons_elem.findall("person")) == 1
        
        person_elem = persons_elem.find("person")
        assert person_elem.get("last_name") == "DUPONT"
        assert person_elem.get("first_name") == "Jean"
        assert person_elem.get("gender") == "m"
    
    def test_export_to_string_with_dates(self):
        """Test d'export avec des dates."""
        exporter = XMLExporter()
        genealogy = Genealogy()
        
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            birth_date=Date(year=1950, month=3, day=15),
            death_date=Date(year=2020, month=12, day=25)
        )
        genealogy.add_person(person)
        
        result = exporter.export_to_string(genealogy)
        root = ET.fromstring(result)
        
        person_elem = root.find("persons/person")
        birth_elem = person_elem.find("birth")
        death_elem = person_elem.find("death")
        
        assert birth_elem is not None
        assert birth_elem.get("year") == "1950"
        assert birth_elem.get("month") == "3"
        assert birth_elem.get("day") == "15"
        
        assert death_elem is not None
        assert death_elem.get("year") == "2020"
        assert death_elem.get("month") == "12"
        assert death_elem.get("day") == "25"
    
    def test_export_to_string_with_family(self):
        """Test d'export avec une famille."""
        exporter = XMLExporter()
        genealogy = Genealogy()
        
        husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        child = Person(last_name="DUPONT", first_name="Pierre", gender=Gender.MALE)
        
        genealogy.add_person(husband)
        genealogy.add_person(wife)
        genealogy.add_person(child)
        
        family = Family(family_id="FAM001", husband_id=husband.unique_id, wife_id=wife.unique_id)
        family.add_child(child.unique_id)
        genealogy.add_family(family)
        
        result = exporter.export_to_string(genealogy)
        root = ET.fromstring(result)
        
        persons_elem = root.find("persons")
        families_elem = root.find("families")
        
        assert len(persons_elem.findall("person")) == 3
        assert len(families_elem.findall("family")) == 1
        
        family_elem = families_elem.find("family")
        assert family_elem.get("husband_id") is not None
        assert family_elem.get("wife_id") is not None
        
        children_elem = family_elem.find("children")
        assert children_elem is not None
        assert len(children_elem.findall("child")) == 1
    
    def test_export_to_string_with_events(self):
        """Test d'export avec des événements."""
        exporter = XMLExporter()
        genealogy = Genealogy()
        
        person = Person(last_name="DUPONT", first_name="Jean")
        event = Event(
            event_type=EventType.GRADUATION,
            date=Date(year=1972, month=6),
            place="Université de Paris",
            notes=["Diplôme d'ingénieur"]
        )
        person.add_event(event)
        genealogy.add_person(person)
        
        result = exporter.export_to_string(genealogy)
        root = ET.fromstring(result)
        
        person_elem = root.find("persons/person")
        events_elem = person_elem.find("events")
        
        assert events_elem is not None
        assert len(events_elem.findall("event")) == 1
        
        event_elem = events_elem.find("event")
        assert event_elem.get("type") == "grad"
        assert event_elem.find("place").text == "Université de Paris"
        notes_elem = event_elem.find("notes")
        assert notes_elem is not None
        note_elem = notes_elem.find("note")
        assert note_elem.text == "Diplôme d'ingénieur"
    
    def test_export_to_file(self):
        """Test d'export vers fichier."""
        exporter = XMLExporter()
        genealogy = Genealogy()
        
        person = Person(last_name="DUPONT", first_name="Jean")
        genealogy.add_person(person)
        
        temp_file = Path("temp_test.xml")
        
        try:
            exporter.export(genealogy, str(temp_file))
            assert temp_file.exists()
            
            # Vérifier le contenu
            root = ET.parse(str(temp_file)).getroot()
            assert root.tag == "genealogy"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_export_empty_genealogy(self):
        """Test d'export d'une généalogie vide."""
        exporter = XMLExporter()
        genealogy = Genealogy()
        
        with pytest.raises(ConversionError, match="La généalogie est vide"):
            exporter.export_to_string(genealogy)
    
    def test_export_invalid_genealogy(self):
        """Test d'export d'un objet invalide."""
        exporter = XMLExporter()
        
        with pytest.raises(ConversionError, match="n'est pas une instance de Genealogy"):
            exporter.export_to_string("invalid")


class TestXMLImporter:
    """Tests pour la classe XMLImporter."""
    
    def test_init(self):
        """Test de l'initialisation."""
        importer = XMLImporter(encoding="utf-8")
        assert importer.encoding == "utf-8"
    
    def test_import_from_string_simple(self):
        """Test d'import depuis chaîne simple."""
        importer = XMLImporter()
        
        xml_string = '''<?xml version="1.0" encoding="utf-8"?>
        <genealogy version="1.0.0" format="geneweb-py-xml">
            <metadata>
                <statistics persons_count="1" families_count="0" events_count="0"/>
            </metadata>
            <persons>
                <person id="1" last_name="DUPONT" first_name="Jean" gender="m"/>
            </persons>
            <families/>
        </genealogy>'''
        
        genealogy = importer.import_from_string(xml_string)
        
        assert len(genealogy.persons) == 1
        person = list(genealogy.persons.values())[0]
        assert person.last_name == "DUPONT"
        assert person.first_name == "Jean"
        assert person.gender == Gender.MALE
    
    def test_import_from_string_with_dates(self):
        """Test d'import avec des dates."""
        importer = XMLImporter()
        
        xml_string = '''<?xml version="1.0" encoding="utf-8"?>
        <genealogy version="1.0.0" format="geneweb-py-xml">
            <metadata>
                <statistics persons_count="1" families_count="0" events_count="0"/>
            </metadata>
            <persons>
                <person id="1" last_name="DUPONT" first_name="Jean">
                    <birth year="1950" month="3" day="15"/>
                    <death year="2020" month="12" day="25"/>
                </person>
            </persons>
            <families/>
        </genealogy>'''
        
        genealogy = importer.import_from_string(xml_string)
        
        person = list(genealogy.persons.values())[0]
        assert person.birth_date.year == 1950
        assert person.birth_date.month == 3
        assert person.birth_date.day == 15
        assert person.death_date.year == 2020
        assert person.death_date.month == 12
        assert person.death_date.day == 25
    
    def test_import_from_string_with_events(self):
        """Test d'import avec des événements."""
        importer = XMLImporter()
        
        xml_string = '''<?xml version="1.0" encoding="utf-8"?>
        <genealogy version="1.0.0" format="geneweb-py-xml">
            <metadata>
                <statistics persons_count="1" families_count="0" events_count="1"/>
            </metadata>
            <persons>
                <person id="1" last_name="DUPONT" first_name="Jean">
                    <events>
                        <event type="grad">
                            <date year="1972" month="6"/>
                            <place>Université de Paris</place>
                            <notes>
                                <note>Diplôme d'ingénieur</note>
                            </notes>
                        </event>
                    </events>
                </person>
            </persons>
            <families/>
        </genealogy>'''
        
        genealogy = importer.import_from_string(xml_string)
        
        person = list(genealogy.persons.values())[0]
        assert len(person.events) == 1
        event = person.events[0]
        assert event.event_type == EventType.GRADUATION
        assert event.place == "Université de Paris"
        assert "Diplôme d'ingénieur" in event.notes
        assert event.date.year == 1972
        assert event.date.month == 6
    
    def test_import_from_file(self):
        """Test d'import depuis fichier."""
        importer = XMLImporter()
        
        xml_string = '''<?xml version="1.0" encoding="utf-8"?>
        <genealogy version="1.0.0" format="geneweb-py-xml">
            <metadata>
                <statistics persons_count="1" families_count="0" events_count="0"/>
            </metadata>
            <persons>
                <person id="1" last_name="DUPONT" first_name="Jean"/>
            </persons>
            <families/>
        </genealogy>'''
        
        temp_file = Path("temp_test.xml")
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(xml_string)
            
            genealogy = importer.import_from_file(str(temp_file))
            assert len(genealogy.persons) == 1
            assert list(genealogy.persons.values())[0].last_name == "DUPONT"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_import_invalid_xml(self):
        """Test d'import de XML invalide."""
        importer = XMLImporter()
        
        with pytest.raises(ConversionError, match="Erreur lors du parsing XML"):
            importer.import_from_string("invalid xml")
    
    def test_import_nonexistent_file(self):
        """Test d'import d'un fichier inexistant."""
        importer = XMLImporter()
        
        with pytest.raises(ConversionError, match="Le fichier n'existe pas"):
            importer.import_from_file("nonexistent.xml")
    
    def test_roundtrip_export_import(self):
        """Test d'export puis import (roundtrip)."""
        # Créer une généalogie
        genealogy = Genealogy()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE,
            birth_date=Date(year=1950, month=3, day=15),
            birth_place="Paris, France"
        )
        event = Event(
            event_type=EventType.GRADUATION,
            date=Date(year=1972, month=6),
            place="Université de Paris",
            notes=["Diplôme d'ingénieur"]
        )
        person.add_event(event)
        genealogy.add_person(person)
        
        # Exporter
        exporter = XMLExporter()
        xml_string = exporter.export_to_string(genealogy)
        
        # Importer
        importer = XMLImporter()
        imported_genealogy = importer.import_from_string(xml_string)
        
        # Vérifier que les données sont identiques
        assert len(imported_genealogy.persons) == 1
        imported_person = list(imported_genealogy.persons.values())[0]
        assert imported_person.last_name == "DUPONT"
        assert imported_person.first_name == "Jean"
        assert imported_person.gender == Gender.MALE
        assert imported_person.birth_date.year == 1950
        assert imported_person.birth_place == "Paris, France"
        assert len(imported_person.events) == 1
        assert imported_person.events[0].event_type == EventType.GRADUATION
