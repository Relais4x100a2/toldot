"""
Tests simples pour les convertisseurs - tests qui fonctionnent
"""

import pytest
import json
import xml.etree.ElementTree as ET
import tempfile
import os
from pathlib import Path
from geneweb_py.formats.json import JSONExporter, JSONImporter
from geneweb_py.formats.xml import XMLExporter, XMLImporter
from geneweb_py.formats.gedcom import GEDCOMExporter, GEDCOMImporter
from geneweb_py.formats.base import ConversionError
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.family import Family, MarriageStatus
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
        birth_place="Paris",
    )
    genealogy.add_person(person1)

    person2 = Person(
        last_name="MARTIN",
        first_name="Marie",
        gender=Gender.FEMALE,
        birth_date=Date(day=20, month=8, year=1992),
        birth_place="Lyon",
    )
    genealogy.add_person(person2)

    # Ajouter une famille
    family = Family(
        family_id="family_1",
        husband_id=person1.unique_id,
        wife_id=person2.unique_id,
        marriage_status=MarriageStatus.MARRIED,
        marriage_date=Date(day=10, month=5, year=2015),
        marriage_place="Marseille",
    )
    genealogy.add_family(family)

    return genealogy


class TestJSONConverter:
    """Tests pour le convertisseur JSON."""

    def test_json_export_to_file(self, sample_genealogy):
        """Test export JSON vers fichier."""
        exporter = JSONExporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            exporter.export(sample_genealogy, temp_path)

            # Vérifier que le fichier a été créé
            assert os.path.exists(temp_path)

            # Vérifier le contenu JSON
            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "persons" in data
            assert "families" in data
            assert len(data["persons"]) == 2
            assert len(data["families"]) == 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_json_export_to_string(self, sample_genealogy):
        """Test export JSON vers chaîne."""
        exporter = JSONExporter()

        json_string = exporter.export_to_string(sample_genealogy)

        # Vérifier que c'est du JSON valide
        data = json.loads(json_string)
        assert "persons" in data
        assert "families" in data

    def test_json_import_from_file(self, sample_genealogy):
        """Test import JSON depuis fichier."""
        # D'abord exporter vers un fichier
        exporter = JSONExporter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
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

    def test_json_import_from_string(self, sample_genealogy):
        """Test import JSON depuis chaîne."""
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

    def test_json_export_invalid_genealogy(self):
        """Test export JSON avec généalogie invalide."""
        exporter = JSONExporter()

        with pytest.raises(ConversionError):
            exporter.export(None, "test.json")

    def test_json_import_invalid_json(self):
        """Test import JSON avec JSON invalide."""
        importer = JSONImporter()

        with pytest.raises(ConversionError):
            importer.import_from_string("invalid json")


class TestXMLConverter:
    """Tests pour le convertisseur XML."""

    def test_xml_export_to_file(self, sample_genealogy):
        """Test export XML vers fichier."""
        exporter = XMLExporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            temp_path = f.name

        try:
            exporter.export(sample_genealogy, temp_path)

            # Vérifier que le fichier a été créé
            assert os.path.exists(temp_path)

            # Vérifier le contenu XML
            tree = ET.parse(temp_path)
            root = tree.getroot()

            assert root.tag == "genealogy"
            assert len(root.findall("persons/person")) == 2
            assert len(root.findall("families/family")) == 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_xml_export_to_string(self, sample_genealogy):
        """Test export XML vers chaîne."""
        exporter = XMLExporter()

        xml_string = exporter.export_to_string(sample_genealogy)

        # Vérifier que c'est du XML valide
        root = ET.fromstring(xml_string)
        assert root.tag == "genealogy"
        assert len(root.findall("persons/person")) == 2
        assert len(root.findall("families/family")) == 1

    def test_xml_import_from_file(self, sample_genealogy):
        """Test import XML depuis fichier."""
        # D'abord exporter vers un fichier
        exporter = XMLExporter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            temp_path = f.name

        try:
            exporter.export(sample_genealogy, temp_path)

            # Maintenant importer
            importer = XMLImporter()
            imported_genealogy = importer.import_from_file(temp_path)

            # Vérifier que la généalogie a été importée
            assert imported_genealogy is not None
            assert len(imported_genealogy.persons) == 2
            assert len(imported_genealogy.families) == 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_xml_import_from_string(self, sample_genealogy):
        """Test import XML depuis chaîne."""
        # D'abord exporter vers une chaîne
        exporter = XMLExporter()
        xml_string = exporter.export_to_string(sample_genealogy)

        # Maintenant importer
        importer = XMLImporter()
        imported_genealogy = importer.import_from_string(xml_string)

        # Vérifier que la généalogie a été importée
        assert imported_genealogy is not None
        assert len(imported_genealogy.persons) == 2
        assert len(imported_genealogy.families) == 1

    def test_xml_export_invalid_genealogy(self):
        """Test export XML avec généalogie invalide."""
        exporter = XMLExporter()

        with pytest.raises(ConversionError):
            exporter.export(None, "test.xml")

    def test_xml_import_invalid_xml(self):
        """Test import XML avec XML invalide."""
        importer = XMLImporter()

        with pytest.raises(ConversionError):
            importer.import_from_string("invalid xml")


class TestGEDCOMConverter:
    """Tests pour le convertisseur GEDCOM."""

    def test_gedcom_export_to_file(self, sample_genealogy):
        """Test export GEDCOM vers fichier."""
        exporter = GEDCOMExporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ged", delete=False) as f:
            temp_path = f.name

        try:
            exporter.export(sample_genealogy, temp_path)

            # Vérifier que le fichier a été créé
            assert os.path.exists(temp_path)

            # Vérifier le contenu GEDCOM
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "0 HEAD" in content
            assert "1 GEDC" in content
            assert "2 VERS" in content
            assert "0 I0001 INDI" in content  # Personne 1
            assert "0 I0002 INDI" in content  # Personne 2
            assert "0 F0001 FAM" in content  # Famille 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_gedcom_export_to_string(self, sample_genealogy):
        """Test export GEDCOM vers chaîne."""
        exporter = GEDCOMExporter()

        gedcom_string = exporter.export_to_string(sample_genealogy)

        # Vérifier le contenu GEDCOM
        assert "0 HEAD" in gedcom_string
        assert "1 GEDC" in gedcom_string
        assert "2 VERS" in gedcom_string
        assert "0 I0001 INDI" in gedcom_string
        assert "0 I0002 INDI" in gedcom_string
        assert "0 F0001 FAM" in gedcom_string

    def test_gedcom_export_invalid_genealogy(self):
        """Test export GEDCOM avec généalogie invalide."""
        exporter = GEDCOMExporter()

        with pytest.raises(ConversionError):
            exporter.export(None, "test.ged")

    def test_gedcom_import_from_nonexistent_file(self):
        """Test import GEDCOM depuis fichier inexistant."""
        importer = GEDCOMImporter()

        with pytest.raises(ConversionError):
            importer.import_from_file("nonexistent.ged")
