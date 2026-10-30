"""
Tests pour le convertisseur GEDCOM
"""

import os
import re
import tempfile

import pytest

from geneweb_py.core.date import CalendarType, Date, DatePrefix
from geneweb_py.core.event import Event, EventType
from geneweb_py.core.family import Child, ChildSex, Family, MarriageStatus
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


class TestGEDCOMExporterCalendars:
    """Export des dates selon le calendrier (mois 13 républicain inclus)."""

    @staticmethod
    def _birth_date_line(date):
        person = Person(last_name="DUPONT", first_name="Jean", birth_date=date)
        genealogy = Genealogy()
        genealogy.add_person(person)
        content = GEDCOMExporter().export_to_string(genealogy)
        lines = content.splitlines()
        return lines[lines.index("1 BIRT") + 1]

    def test_gregorian_date_unchanged(self):
        line = self._birth_date_line(Date(day=15, month=6, year=1990))
        assert line == "2 DATE 15 JUN 1990"

    def test_french_republican_complementary_month_does_not_crash(self):
        date = Date(day=3, month=13, year=7, calendar=CalendarType.FRENCH_REPUBLICAN)
        line = self._birth_date_line(date)
        assert line == "2 DATE @#DFRENCH R@ 3 COMP 7"

    def test_french_republican_regular_month(self):
        date = Date(day=18, month=2, year=8, calendar=CalendarType.FRENCH_REPUBLICAN)
        line = self._birth_date_line(date)
        assert line == "2 DATE @#DFRENCH R@ 18 BRUM 8"


class TestGEDCOMExporterMultilineNotes:
    """Les notes multi-lignes doivent rester du GEDCOM valide (CONT)."""

    @staticmethod
    def _export(person):
        genealogy = Genealogy()
        genealogy.add_person(person)
        return GEDCOMExporter().export_to_string(genealogy)

    @staticmethod
    def _assert_every_line_has_level(content):
        for number, line in enumerate(content.splitlines(), start=1):
            assert re.match(r"^\d+ ", line), f"ligne {number} sans niveau GEDCOM"

    def test_person_note_with_newline_stays_valid_gedcom(self):
        person = Person(last_name="DUPONT", first_name="Jean")
        person.notes.append("Première ligne\nDeuxième ligne")
        self._assert_every_line_has_level(self._export(person))

    def test_person_note_round_trip_keeps_line_breaks(self):
        person = Person(last_name="DUPONT", first_name="Jean")
        person.notes.append("Première ligne\nDeuxième ligne")
        content = self._export(person)
        reloaded = GEDCOMImporter().import_from_string(content)
        (restored,) = reloaded.persons.values()
        assert "\n".join(restored.notes) == "Première ligne\nDeuxième ligne"

    def test_event_note_with_newline_stays_valid_gedcom(self):
        person = Person(last_name="DUPONT", first_name="Jean")
        person.events.append(
            Event(
                event_type=EventType.BIRTH,
                place="Paris",
                notes=["Ligne A\nLigne B\r\nLigne C"],
            )
        )
        self._assert_every_line_has_level(self._export(person))

    def test_single_line_notes_unchanged(self):
        person = Person(last_name="DUPONT", first_name="Jean")
        person.notes.append("Une seule ligne")
        assert "2 CONT Une seule ligne" in self._export(person).splitlines()


class TestGEDCOMDatePrefixAndCalendarRoundTrip:
    """Préfixes (vers/avant/après) et calendrier républicain : export puis ré-import."""

    @staticmethod
    def _export_line_and_reloaded_date(date):
        person = Person(last_name="DUPONT", first_name="Jean", birth_date=date)
        genealogy = Genealogy()
        genealogy.add_person(person)
        content = GEDCOMExporter().export_to_string(genealogy)
        lines = content.splitlines()
        line = lines[lines.index("1 BIRT") + 1]
        (restored,) = GEDCOMImporter().import_from_string(content).persons.values()
        return line, restored.birth_date

    @pytest.mark.parametrize(
        ("prefix", "keyword"),
        [
            (DatePrefix.ABOUT, "ABT"),
            (DatePrefix.BEFORE, "BEF"),
            (DatePrefix.AFTER, "AFT"),
            (DatePrefix.MAYBE, "EST"),
        ],
    )
    def test_prefix_is_exported(self, prefix, keyword):
        line, _ = self._export_line_and_reloaded_date(Date(year=1850, prefix=prefix))
        assert line == f"2 DATE {keyword} 1850"

    @pytest.mark.parametrize(
        "prefix", [DatePrefix.ABOUT, DatePrefix.BEFORE, DatePrefix.AFTER]
    )
    def test_prefix_survives_round_trip(self, prefix):
        _, restored = self._export_line_and_reloaded_date(
            Date(day=3, month=5, year=1850, prefix=prefix)
        )
        assert (restored.day, restored.month, restored.year) == (3, 5, 1850)
        assert restored.prefix == prefix

    def test_maybe_prefix_is_exported_as_estimated_and_read_back_as_about(self):
        _, restored = self._export_line_and_reloaded_date(
            Date(year=1850, prefix=DatePrefix.MAYBE)
        )
        assert restored.prefix == DatePrefix.ABOUT

    def test_prefix_comes_before_calendar_escape(self):
        date = Date(
            day=3,
            month=13,
            year=7,
            prefix=DatePrefix.ABOUT,
            calendar=CalendarType.FRENCH_REPUBLICAN,
        )
        line, _ = self._export_line_and_reloaded_date(date)
        assert line == "2 DATE ABT @#DFRENCH R@ 3 COMP 7"

    @pytest.mark.parametrize(
        ("day", "month", "year"),
        [(3, 13, 7), (18, 2, 8), (None, 2, 8), (None, None, 8)],
    )
    def test_french_republican_date_survives_round_trip(self, day, month, year):
        date = Date(
            day=day, month=month, year=year, calendar=CalendarType.FRENCH_REPUBLICAN
        )
        _, restored = self._export_line_and_reloaded_date(date)
        assert restored.calendar == CalendarType.FRENCH_REPUBLICAN
        assert (restored.day, restored.month, restored.year) == (day, month, year)

    def test_prefixed_republican_date_survives_round_trip(self):
        date = Date(
            day=3,
            month=13,
            year=7,
            prefix=DatePrefix.BEFORE,
            calendar=CalendarType.FRENCH_REPUBLICAN,
        )
        _, restored = self._export_line_and_reloaded_date(date)
        assert restored.prefix == DatePrefix.BEFORE
        assert restored.calendar == CalendarType.FRENCH_REPUBLICAN
        assert (restored.day, restored.month, restored.year) == (3, 13, 7)

    def test_plain_gregorian_date_unchanged(self):
        line, restored = self._export_line_and_reloaded_date(
            Date(day=15, month=6, year=1990)
        )
        assert line == "2 DATE 15 JUN 1990"
        assert restored.prefix is None
        assert restored.calendar == CalendarType.GREGORIAN


class TestGEDCOMBetweenAndHebrewDates:
    """Intervalles BET ... AND ... et calendrier hébreu (@#DHEBREW@)."""

    _HEBREW_MONTHS = [
        "TSH", "CSH", "KSL", "TVT", "SHV", "ADR", "ADS",
        "NSN", "IYR", "SVN", "TMZ", "AAV", "ELL",
    ]  # fmt: skip

    @staticmethod
    def _export_line_and_reloaded_date(date):
        person = Person(last_name="DUPONT", first_name="Jean", birth_date=date)
        genealogy = Genealogy()
        genealogy.add_person(person)
        content = GEDCOMExporter().export_to_string(genealogy)
        lines = content.splitlines()
        line = lines[lines.index("1 BIRT") + 1]
        (restored,) = GEDCOMImporter().import_from_string(content).persons.values()
        return line, restored.birth_date

    def test_between_years_is_exported(self):
        date = Date(
            year=1850, prefix=DatePrefix.BETWEEN, alternative_dates=[Date(year=1860)]
        )
        line, _ = self._export_line_and_reloaded_date(date)
        assert line == "2 DATE BET 1850 AND 1860"

    def test_between_full_dates_round_trip(self):
        date = Date(
            day=3,
            month=5,
            year=1850,
            prefix=DatePrefix.BETWEEN,
            alternative_dates=[Date(day=5, month=6, year=1860)],
        )
        line, restored = self._export_line_and_reloaded_date(date)
        assert line == "2 DATE BET 3 MAY 1850 AND 5 JUN 1860"
        assert restored.prefix == DatePrefix.BETWEEN
        assert (restored.day, restored.month, restored.year) == (3, 5, 1850)
        (end,) = restored.alternative_dates
        assert (end.day, end.month, end.year) == (5, 6, 1860)

    def test_between_without_end_bound_is_written_as_plain_date(self):
        date = Date(year=1850, prefix=DatePrefix.BETWEEN)
        line, _ = self._export_line_and_reloaded_date(date)
        assert line == "2 DATE 1850"

    def test_between_republican_round_trip_keeps_calendar_on_main_date(self):
        date = Date(
            day=3,
            month=13,
            year=7,
            prefix=DatePrefix.BETWEEN,
            calendar=CalendarType.FRENCH_REPUBLICAN,
            alternative_dates=[Date(day=1, month=1, year=8)],
        )
        line, restored = self._export_line_and_reloaded_date(date)
        assert line == "2 DATE BET @#DFRENCH R@ 3 COMP 7 AND @#DFRENCH R@ 1 VEND 8"
        assert restored.prefix == DatePrefix.BETWEEN
        assert restored.calendar == CalendarType.FRENCH_REPUBLICAN
        (end,) = restored.alternative_dates
        assert (end.day, end.month, end.year) == (1, 1, 8)
        assert end.calendar == CalendarType.GREGORIAN

    def test_malformed_between_is_still_ignored_on_import(self):
        content = (
            "0 HEAD\n0 @I1@ INDI\n1 NAME Jean /DUPONT/\n1 BIRT\n2 DATE BET 1850\n0 TRLR"
        )
        (person,) = GEDCOMImporter().import_from_string(content).persons.values()
        assert person.birth_date is None

    @pytest.mark.parametrize("month", range(1, 14))
    def test_hebrew_month_round_trip(self, month):
        date = Date(day=15, month=month, year=5750, calendar=CalendarType.HEBREW)
        line, restored = self._export_line_and_reloaded_date(date)
        assert line == f"2 DATE @#DHEBREW@ 15 {self._HEBREW_MONTHS[month - 1]} 5750"
        assert restored.calendar == CalendarType.HEBREW
        assert (restored.day, restored.month, restored.year) == (15, month, 5750)

    def test_hebrew_year_only_and_prefix_round_trip(self):
        date = Date(year=5750, prefix=DatePrefix.ABOUT, calendar=CalendarType.HEBREW)
        line, restored = self._export_line_and_reloaded_date(date)
        assert line == "2 DATE ABT @#DHEBREW@ 5750"
        assert restored.prefix == DatePrefix.ABOUT
        assert restored.calendar == CalendarType.HEBREW
        assert restored.year == 5750


class TestGEDCOMFamilyLinks:
    """Les fiches INDI pointent en retour vers leurs familles (FAMS / FAMC)."""

    @staticmethod
    def _genealogy():
        genealogy = Genealogy()
        father = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        mother = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        stepmother = Person(last_name="DURAND", first_name="Anne", gender=Gender.FEMALE)
        child = Person(last_name="DUPONT", first_name="Paul", gender=Gender.MALE)
        for person in (father, mother, stepmother, child):
            genealogy.add_person(person)
        first = Family(
            family_id="f1", husband_id=father.unique_id, wife_id=mother.unique_id
        )
        first.children.append(Child(person_id=child.unique_id, sex=ChildSex.MALE))
        second = Family(
            family_id="f2", husband_id=father.unique_id, wife_id=stepmother.unique_id
        )
        genealogy.add_family(first)
        genealogy.add_family(second)
        return genealogy

    @staticmethod
    def _blocks(content):
        """Retourne {xref: [lignes de niveau 1]} pour chaque enregistrement."""
        blocks, current = {}, None
        for line in content.splitlines():
            if line.startswith("0 "):
                parts = line.split()
                current = parts[1] if len(parts) > 2 else None
                if current:
                    blocks[current] = []
            elif current and line.startswith("1 "):
                blocks[current].append(line)
        return blocks

    @staticmethod
    def _targets(lines, tag):
        return [
            line.split()[2].strip("@") for line in lines if line.startswith(f"1 {tag} ")
        ]

    def test_spouse_gets_one_fams_per_union(self):
        blocks = self._blocks(GEDCOMExporter().export_to_string(self._genealogy()))
        assert self._targets(blocks["I0001"], "FAMS") == ["F0001", "F0002"]
        assert self._targets(blocks["I0002"], "FAMS") == ["F0001"]

    def test_child_gets_famc(self):
        blocks = self._blocks(GEDCOMExporter().export_to_string(self._genealogy()))
        assert self._targets(blocks["I0004"], "FAMC") == ["F0001"]
        assert self._targets(blocks["I0001"], "FAMC") == []

    def test_family_links_are_symmetric_with_fam_records(self):
        blocks = self._blocks(GEDCOMExporter().export_to_string(self._genealogy()))
        for xref, lines in blocks.items():
            if not xref.startswith("I"):
                continue
            for fam in self._targets(lines, "FAMS"):
                assert fam in blocks
                fam_lines = blocks[fam]
                assert any(
                    t in ("HUSB", "WIFE") for t in [x.split()[1] for x in fam_lines]
                )
            for fam in self._targets(lines, "FAMC"):
                assert any(x.startswith("1 CHIL ") for x in blocks[fam])

    def test_round_trip_keeps_person_family_links(self):
        genealogy = self._genealogy()
        reloaded = GEDCOMImporter().import_from_string(
            GEDCOMExporter().export_to_string(genealogy)
        )
        spouse_counts = sorted(
            len(p.families_as_spouse) for p in reloaded.persons.values()
        )
        child_counts = sorted(
            len(p.families_as_child) for p in reloaded.persons.values()
        )
        assert spouse_counts == [0, 1, 1, 2]
        assert child_counts == [0, 0, 0, 1]
