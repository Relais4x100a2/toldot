"""
Tests pour le convertisseur GEDCOM
"""

import os
import tempfile

import pytest

from geneweb_py.core.date import Date
from geneweb_py.core.family import Family, MarriageStatus
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Gender, Person
from geneweb_py.formats.gedcom import ConversionError, GEDCOMExporter, GEDCOMImporter


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


class TestGEDCOMExporter:
    """Tests pour GEDCOMExporter."""

    def test_export_to_file(self, sample_genealogy):
        """Test export vers un fichier GEDCOM."""
        exporter = GEDCOMExporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ged", delete=False) as f:
            temp_path = f.name

        try:
            exporter.export(sample_genealogy, temp_path)

            # Vérifier que le fichier a été créé
            assert os.path.exists(temp_path)

            # Vérifier le contenu GEDCOM
            with open(temp_path, encoding="utf-8") as f:
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

    def test_export_to_string(self, sample_genealogy):
        """Test export vers une chaîne GEDCOM."""
        exporter = GEDCOMExporter()

        gedcom_string = exporter.export_to_string(sample_genealogy)

        # Vérifier le contenu GEDCOM
        assert "0 HEAD" in gedcom_string
        assert "1 GEDC" in gedcom_string
        assert "2 VERS" in gedcom_string
        assert "0 I0001 INDI" in gedcom_string
        assert "0 I0002 INDI" in gedcom_string
        assert "0 F0001 FAM" in gedcom_string

    def test_export_with_custom_settings(self, sample_genealogy):
        """Test export avec paramètres personnalisés."""
        exporter = GEDCOMExporter(version="5.5.1")

        gedcom_string = exporter.export_to_string(sample_genealogy)

        # Vérifier que c'est du GEDCOM valide
        assert "0 HEAD" in gedcom_string
        assert "2 VERS 5.5.1" in gedcom_string

    def test_export_invalid_genealogy(self):
        """Test export avec généalogie invalide."""
        exporter = GEDCOMExporter()

        with pytest.raises(ConversionError):
            exporter.export(None, "test.ged")

    def test_export_to_invalid_path(self, sample_genealogy):
        """Test export vers chemin invalide."""
        exporter = GEDCOMExporter()

        with pytest.raises(ConversionError):
            exporter.export(sample_genealogy, "/invalid/path/test.ged")


class TestGEDCOMImporter:
    """Tests pour GEDCOMImporter."""

    def test_import_from_file(self, sample_genealogy):
        """Test import depuis un fichier GEDCOM."""
        # D'abord exporter vers un fichier
        exporter = GEDCOMExporter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ged", delete=False) as f:
            temp_path = f.name

        try:
            exporter.export(sample_genealogy, temp_path)

            importer = GEDCOMImporter()
            imported_genealogy = importer.import_from_file(temp_path)

            assert len(imported_genealogy.persons) == 2
            assert len(imported_genealogy.families) == 1
            p1 = imported_genealogy.find_person("DUPONT", "Jean", 0)
            p2 = imported_genealogy.find_person("MARTIN", "Marie", 0)
            assert p1 is not None and p2 is not None
            assert p1.birth_date is not None and p1.birth_date.year == 1990
            assert p2.birth_date is not None and p2.birth_date.year == 1992
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_import_from_string(self, sample_genealogy):
        """Test import depuis une chaîne GEDCOM."""
        exporter = GEDCOMExporter()
        gedcom_string = exporter.export_to_string(sample_genealogy)

        importer = GEDCOMImporter()
        imported_genealogy = importer.import_from_string(gedcom_string)

        assert len(imported_genealogy.persons) == 2
        assert len(imported_genealogy.families) == 1
        fam = next(iter(imported_genealogy.families.values()))
        assert fam.husband_id and fam.wife_id

    def test_import_invalid_gedcom(self):
        """Test import avec GEDCOM invalide (lignes non structurées)."""
        importer = GEDCOMImporter()

        result = importer.import_from_string("invalid gedcom")
        assert result is not None
        assert len(result.persons) == 0
        """Test import depuis fichier inexistant."""
        importer = GEDCOMImporter()

        with pytest.raises(ConversionError):
            importer.import_from_file("nonexistent.ged")

    def test_import_empty_gedcom(self):
        """Test import avec GEDCOM vide."""
        importer = GEDCOMImporter()

        result = importer.import_from_string("")
        assert result is not None
        assert len(result.persons) == 0


class TestGEDCOMConverterIntegration:
    """Tests d'intégration pour le convertisseur GEDCOM."""

    def test_round_trip_conversion(self, sample_genealogy):
        """Test conversion aller-retour (export puis import)."""
        exporter = GEDCOMExporter()
        importer = GEDCOMImporter()

        # Export
        gedcom_string = exporter.export_to_string(sample_genealogy)

        # Import
        imported_genealogy = importer.import_from_string(gedcom_string)

        assert len(imported_genealogy.persons) == len(sample_genealogy.persons)
        assert len(imported_genealogy.families) == len(sample_genealogy.families)
        imp1 = imported_genealogy.find_person("DUPONT", "Jean", 0)
        assert imp1 is not None
        assert imp1.birth_place == "Paris"
