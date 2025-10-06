"""
Tests unitaires pour les convertisseurs JSON.
"""

import json
import pytest
from pathlib import Path

from geneweb_py.formats.json import JSONExporter, JSONImporter, ConversionError
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person
from geneweb_py.core.family import Family
from geneweb_py.core.date import Date
from geneweb_py.core.event import Event


class TestJSONExporter:
    """Tests pour la classe JSONExporter."""
    
    def test_init(self):
        """Test de l'initialisation."""
        exporter = JSONExporter(encoding="utf-8", indent=4, ensure_ascii=True)
        assert exporter.encoding == "utf-8"
        assert exporter.indent == 4
        assert exporter.ensure_ascii is True
    
    def test_export_to_string_simple(self):
        """Test d'export vers chaîne simple."""
        exporter = JSONExporter()
        genealogy = Genealogy()
        
        person = Person(surname="DUPONT", given_name="Jean", sex="M")
        genealogy.add_person(person)
        
        result = exporter.export_to_string(genealogy)
        
        # Vérifier que c'est du JSON valide
        data = json.loads(result)
        assert "metadata" in data
        assert "persons" in data
        assert "families" in data
        assert len(data["persons"]) == 1
        assert data["persons"][0]["surname"] == "DUPONT"
        assert data["persons"][0]["given_name"] == "Jean"
        assert data["persons"][0]["sex"] == "M"
    
    def test_export_to_string_with_dates(self):
        """Test d'export avec des dates."""
        exporter = JSONExporter()
        genealogy = Genealogy()
        
        person = Person(
            surname="DUPONT",
            given_name="Jean",
            birth_date=Date(year=1950, month=3, day=15),
            death_date=Date(year=2020, month=12, day=25)
        )
        genealogy.add_person(person)
        
        result = exporter.export_to_string(genealogy)
        data = json.loads(result)
        
        person_data = data["persons"][0]
        assert person_data["birth_date"]["year"] == 1950
        assert person_data["birth_date"]["month"] == 3
        assert person_data["birth_date"]["day"] == 15
        assert person_data["death_date"]["year"] == 2020
        assert person_data["death_date"]["month"] == 12
        assert person_data["death_date"]["day"] == 25
    
    def test_export_to_string_with_family(self):
        """Test d'export avec une famille."""
        exporter = JSONExporter()
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
        data = json.loads(result)
        
        assert len(data["persons"]) == 3
        assert len(data["families"]) == 1
        
        family_data = data["families"][0]
        assert family_data["husband_id"] is not None
        assert family_data["wife_id"] is not None
        assert len(family_data["children_ids"]) == 1
    
    def test_export_to_string_with_events(self):
        """Test d'export avec des événements."""
        exporter = JSONExporter()
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
        data = json.loads(result)
        
        person_data = data["persons"][0]
        assert len(person_data["events"]) == 1
        event_data = person_data["events"][0]
        assert event_data["event_type"] == "graduation"
        assert event_data["place"] == "Université de Paris"
        assert event_data["description"] == "Diplôme d'ingénieur"
    
    def test_export_to_file(self):
        """Test d'export vers fichier."""
        exporter = JSONExporter()
        genealogy = Genealogy()
        
        person = Person(surname="DUPONT", given_name="Jean")
        genealogy.add_person(person)
        
        temp_file = Path("temp_test.json")
        
        try:
            exporter.export(genealogy, str(temp_file))
            assert temp_file.exists()
            
            # Vérifier le contenu
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert len(data["persons"]) == 1
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_export_empty_genealogy(self):
        """Test d'export d'une généalogie vide."""
        exporter = JSONExporter()
        genealogy = Genealogy()
        
        with pytest.raises(ConversionError, match="La généalogie est vide"):
            exporter.export_to_string(genealogy)
    
    def test_export_invalid_genealogy(self):
        """Test d'export d'un objet invalide."""
        exporter = JSONExporter()
        
        with pytest.raises(ConversionError, match="n'est pas une instance de Genealogy"):
            exporter.export_to_string("invalid")


class TestJSONImporter:
    """Tests pour la classe JSONImporter."""
    
    def test_init(self):
        """Test de l'initialisation."""
        importer = JSONImporter(encoding="utf-8")
        assert importer.encoding == "utf-8"
    
    def test_import_from_string_simple(self):
        """Test d'import depuis chaîne simple."""
        importer = JSONImporter()
        
        json_data = {
            "metadata": {"version": "1.0.0"},
            "persons": [
                {
                    "id": 1,
                    "surname": "DUPONT",
                    "given_name": "Jean",
                    "sex": "M"
                }
            ],
            "families": []
        }
        
        json_string = json.dumps(json_data)
        genealogy = importer.import_from_string(json_string)
        
        assert len(genealogy.persons) == 1
        person = genealogy.persons[0]
        assert person.surname == "DUPONT"
        assert person.given_name == "Jean"
        assert person.sex == "M"
    
    def test_import_from_string_with_dates(self):
        """Test d'import avec des dates."""
        importer = JSONImporter()
        
        json_data = {
            "metadata": {"version": "1.0.0"},
            "persons": [
                {
                    "id": 1,
                    "surname": "DUPONT",
                    "given_name": "Jean",
                    "birth_date": {
                        "year": 1950,
                        "month": 3,
                        "day": 15
                    },
                    "death_date": {
                        "year": 2020,
                        "month": 12,
                        "day": 25
                    }
                }
            ],
            "families": []
        }
        
        json_string = json.dumps(json_data)
        genealogy = importer.import_from_string(json_string)
        
        person = genealogy.persons[0]
        assert person.birth_date.year == 1950
        assert person.birth_date.month == 3
        assert person.birth_date.day == 15
        assert person.death_date.year == 2020
        assert person.death_date.month == 12
        assert person.death_date.day == 25
    
    def test_import_from_string_with_events(self):
        """Test d'import avec des événements."""
        importer = JSONImporter()
        
        json_data = {
            "metadata": {"version": "1.0.0"},
            "persons": [
                {
                    "id": 1,
                    "surname": "DUPONT",
                    "given_name": "Jean",
                    "events": [
                        {
                            "event_type": "graduation",
                            "date": {"year": 1972, "month": 6},
                            "place": "Université de Paris",
                            "description": "Diplôme d'ingénieur"
                        }
                    ]
                }
            ],
            "families": []
        }
        
        json_string = json.dumps(json_data)
        genealogy = importer.import_from_string(json_string)
        
        person = genealogy.persons[0]
        assert len(person.events) == 1
        event = person.events[0]
        assert event.event_type == "graduation"
        assert event.place == "Université de Paris"
        assert event.description == "Diplôme d'ingénieur"
        assert event.date.year == 1972
        assert event.date.month == 6
    
    def test_import_from_file(self):
        """Test d'import depuis fichier."""
        importer = JSONImporter()
        
        json_data = {
            "metadata": {"version": "1.0.0"},
            "persons": [
                {
                    "id": 1,
                    "surname": "DUPONT",
                    "given_name": "Jean"
                }
            ],
            "families": []
        }
        
        temp_file = Path("temp_test.json")
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f)
            
            genealogy = importer.import_from_file(str(temp_file))
            assert len(genealogy.persons) == 1
            assert genealogy.persons[0].surname == "DUPONT"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_import_invalid_json(self):
        """Test d'import de JSON invalide."""
        importer = JSONImporter()
        
        with pytest.raises(ConversionError, match="Erreur lors du parsing JSON"):
            importer.import_from_string("invalid json")
    
    def test_import_nonexistent_file(self):
        """Test d'import d'un fichier inexistant."""
        importer = JSONImporter()
        
        with pytest.raises(ConversionError, match="Le fichier n'existe pas"):
            importer.import_from_file("nonexistent.json")
    
    def test_roundtrip_export_import(self):
        """Test d'export puis import (roundtrip)."""
        # Créer une généalogie
        genealogy = Genealogy()
        person = Person(
            surname="DUPONT",
            given_name="Jean",
            sex="M",
            birth_date=Date(year=1950, month=3, day=15),
            birth_place="Paris, France"
        )
        event = Event(
            event_type="graduation",
            date=Date(year=1972, month=6),
            place="Université de Paris",
            description="Diplôme d'ingénieur"
        )
        person.add_event(event)
        genealogy.add_person(person)
        
        # Exporter
        exporter = JSONExporter()
        json_string = exporter.export_to_string(genealogy)
        
        # Importer
        importer = JSONImporter()
        imported_genealogy = importer.import_from_string(json_string)
        
        # Vérifier que les données sont identiques
        assert len(imported_genealogy.persons) == 1
        imported_person = imported_genealogy.persons[0]
        assert imported_person.surname == "DUPONT"
        assert imported_person.given_name == "Jean"
        assert imported_person.sex == "M"
        assert imported_person.birth_date.year == 1950
        assert imported_person.birth_place == "Paris, France"
        assert len(imported_person.events) == 1
        assert imported_person.events[0].event_type == "graduation"
