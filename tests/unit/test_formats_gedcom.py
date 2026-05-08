"""
Tests unitaires pour les convertisseurs GEDCOM.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from geneweb_py.core.date import Date, DatePrefix
from geneweb_py.core.event import EventType, FamilyEvent, FamilyEventType, PersonalEvent
from geneweb_py.core.family import Family, MarriageStatus
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Gender, Person, Title
from geneweb_py.formats.gedcom import ConversionError, GEDCOMExporter, GEDCOMImporter


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

        person = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        genealogy.add_person(person)

        result = exporter.export_to_string(genealogy)

        # Vérifier que c'est du GEDCOM valide
        lines = result.split("\n")
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
            last_name="DUPONT",
            first_name="Jean",
            birth_date=Date(year=1950, month=3, day=15),
            death_date=Date(year=2020, month=12, day=25),
        )
        genealogy.add_person(person)

        result = exporter.export_to_string(genealogy)
        lines = result.split("\n")

        # Vérifier la présence de la personne et des dates
        assert any("0 I0001 INDI" in line for line in lines)
        assert any("2 GIVN Jean" in line for line in lines)
        assert any("2 SURN DUPONT" in line for line in lines)
        assert any("2 DATE 15 MAR 1950" in line for line in lines)
        assert any("2 DATE 25 DEC 2020" in line for line in lines)

    def test_export_to_string_with_family(self):
        """Test d'export avec une famille."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()

        husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        child = Person(last_name="DUPONT", first_name="Pierre", gender=Gender.MALE)

        genealogy.add_person(husband)
        genealogy.add_person(wife)
        genealogy.add_person(child)

        family = Family(
            family_id="FAM001", husband_id=husband.unique_id, wife_id=wife.unique_id
        )
        family.add_child(child)
        genealogy.add_family(family)

        result = exporter.export_to_string(genealogy)
        lines = result.split("\n")

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

        person = Person(last_name="DUPONT", first_name="Jean")
        from geneweb_py.core.event import PersonalEvent

        event = PersonalEvent(
            event_type=EventType.GRADUATION,
            date=Date(year=1972, month=6),
            place="Université de Paris",
            notes=["Diplôme d'ingénieur"],
        )
        person.add_event(event)
        genealogy.add_person(person)

        result = exporter.export_to_string(genealogy)
        lines = result.split("\n")

        # Vérifier la présence d'un événement
        assert any("1 GRAD" in line for line in lines)
        assert any("2 DATE JUN 1972" in line for line in lines)
        assert any("2 PLAC Université de Paris" in line for line in lines)
        assert any("2 NOTE Diplôme d'ingénieur" in line for line in lines)

    def test_export_to_file(self):
        """Test d'export vers fichier."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()

        person = Person(last_name="DUPONT", first_name="Jean")
        genealogy.add_person(person)

        temp_file = Path("temp_test.ged")

        try:
            exporter.export(genealogy, str(temp_file))
            assert temp_file.exists()

            # Vérifier le contenu
            with open(temp_file, encoding="utf-8") as f:
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

        with pytest.raises(
            ConversionError, match="n'est pas une instance de Genealogy"
        ):
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

        assert len(genealogy.persons) == 1
        p = genealogy.find_person("DUPONT", "Jean", 0)
        assert p is not None
        assert p.gender == Gender.MALE
        assert p.first_name == "Jean"
        assert p.last_name == "DUPONT"

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
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(gedcom_string)

            genealogy = importer.import_from_file(str(temp_file))
            assert len(genealogy.persons) == 1
            assert genealogy.find_person("DUPONT", "Jean", 0) is not None
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_import_invalid_gedcom(self):
        """Test d'import de GEDCOM invalide (parsing gracieux)."""
        importer = GEDCOMImporter()

        # L'importer GEDCOM fait du parsing gracieux et ignore les tags invalides
        invalid_gedcom = """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 INVALID_TAG
1 INVALID_SUBTAG
2 INVALID_SUBSUBTAG
0 TRLR"""

        # L'import devrait réussir mais retourner une généalogie vide
        genealogy = importer.import_from_string(invalid_gedcom)
        assert isinstance(genealogy, Genealogy)
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0

    def test_import_nonexistent_file(self):
        """Test d'import d'un fichier inexistant."""
        importer = GEDCOMImporter()

        with pytest.raises(ConversionError, match="Le fichier n'existe pas"):
            importer.import_from_file("nonexistent.ged")

    def test_conversion_error_is_geneweb_error(self):
        """Les erreurs d'import GEDCOM héritent de GeneWebError."""
        from geneweb_py.core.exceptions import GeneWebError

        assert issubclass(ConversionError, GeneWebError)

    def test_import_duplicate_indi_raises(self):
        """Deux blocs INDI avec la même xref lèvent ConversionError."""
        from geneweb_py.core.exceptions import GeneWebError

        importer = GEDCOMImporter()
        ged = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME
2 GIVN A
2 SURN A
0 @I1@ INDI
1 NAME
2 GIVN B
2 SURN B
0 TRLR
"""
        with pytest.raises(GeneWebError):
            importer.import_from_string(ged)


# ---------------------------------------------------------------------------
# Tests de couverture complémentaires – GEDCOMExporter
# ---------------------------------------------------------------------------


class TestGEDCOMExporterCoverage:
    """Branches non couvertes de GEDCOMExporter."""

    def test_export_person_with_death_place(self) -> None:
        """Ligne 183 : person.death_place exporté."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        person = Person(
            last_name="DURAND",
            first_name="Marie",
            death_place="Lyon",
        )
        genealogy.add_person(person)
        result = exporter.export_to_string(genealogy)
        assert "2 PLAC Lyon" in result

    def test_export_person_with_titles(self) -> None:
        """Lignes 187-188 : titles exportés."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        person = Person(last_name="BLANC", first_name="Paul")
        person.titles.append(Title(name="Docteur"))
        genealogy.add_person(person)
        result = exporter.export_to_string(genealogy)
        assert "1 TITL Docteur" in result

    def test_export_person_with_occupation(self) -> None:
        """Ligne 191 : occupation exportée."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        person = Person(last_name="NOIR", first_name="Luc", occupation="Médecin")
        genealogy.add_person(person)
        result = exporter.export_to_string(genealogy)
        assert "1 OCCU Médecin" in result

    def test_export_person_with_notes(self) -> None:
        """Lignes 195-197 : notes exportées avec CONT."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        person = Person(last_name="VERT", first_name="Claire")
        person.notes.append("Note importante")
        genealogy.add_person(person)
        result = exporter.export_to_string(genealogy)
        assert "1 NOTE" in result
        assert "2 CONT Note importante" in result

    def test_export_family_with_events(self) -> None:
        """Lignes 229-230 : événements familiaux exportés."""
        exporter = GEDCOMExporter()
        genealogy = Genealogy()
        husband = Person(last_name="PETIT", first_name="Henri", gender=Gender.MALE)
        wife = Person(last_name="GRAND", first_name="Anne", gender=Gender.FEMALE)
        genealogy.add_person(husband)
        genealogy.add_person(wife)
        family = Family(
            family_id="FAM001",
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status=MarriageStatus.MARRIED,
        )
        fe = FamilyEvent(
            event_type=EventType.MARRIAGE,
            family_event_type=FamilyEventType.MARRIAGE,
            date=Date(year=1980, month=6, day=15),
            place="Paris",
        )
        family.events.append(fe)
        genealogy.add_family(family)
        result = exporter.export_to_string(genealogy)
        assert "1 MARR" in result
        assert "2 DATE 15 JUN 1980" in result
        assert "2 PLAC Paris" in result


# ---------------------------------------------------------------------------
# Tests de couverture complémentaires – GEDCOMImporter
# ---------------------------------------------------------------------------


class TestGEDCOMImporterCoverage:
    """Branches non couvertes de GEDCOMImporter."""

    # ---- _normalize_xref_key ----

    def test_normalize_xref_key_with_at_signs(self) -> None:
        """Ligne 365 : @xref@ → xref."""
        assert GEDCOMImporter._normalize_xref_key("@I1@") == "I1"

    def test_normalize_xref_key_plain(self) -> None:
        """Ligne 366 : token sans @ retourné tel quel."""
        assert GEDCOMImporter._normalize_xref_key("I0001") == "I0001"

    # ---- _decode_file_bytes ----

    def test_decode_file_bytes_iso88591(self) -> None:
        """Lignes 371-386 : fallback ISO-8859-1 quand UTF-8 échoue."""
        importer = GEDCOMImporter()
        raw = "0 HEAD\n0 TRLR\n".encode("iso-8859-1")
        # Le BOM UTF-8 est absent, mais la chaîne est ASCII-compatible,
        # donc UTF-8 réussira ; on force avec des octets latin1 non-ASCII.
        raw_latin = bytes([0x30, 0x20, 0x48, 0x45, 0x41, 0x44, 0x0A, 0xE9, 0x0A])
        text, enc = importer._decode_file_bytes(raw_latin)
        assert isinstance(text, str)

    # ---- import_from_file OSError ----

    def test_import_from_file_oserror(self, tmp_path: Path) -> None:
        """Lignes 393-394 : OSError lors de la lecture du fichier."""
        importer = GEDCOMImporter()
        # Créer un fichier puis le rendre inaccessible via mock
        f = tmp_path / "test.ged"
        f.write_text("0 HEAD\n0 TRLR\n", encoding="utf-8")
        with patch("builtins.open", side_effect=OSError("permission denied")):
            with pytest.raises(ConversionError, match="Impossible de lire"):
                importer.import_from_file(str(f))

    # ---- _parse_line edge cases ----

    def test_parse_line_invalid_level(self) -> None:
        """Ligne 509 : niveau non entier lève ConversionError."""
        importer = GEDCOMImporter()
        with pytest.raises(ConversionError):
            importer._parse_line("X HEAD", 1)

    def test_parse_line_unterminated_xref(self) -> None:
        """Ligne 522 : @xref sans fermeture lève ConversionError."""
        importer = GEDCOMImporter()
        with pytest.raises(ConversionError, match="non terminé"):
            importer._parse_line("0 @I1 INDI", 1)

    def test_parse_line_empty_level0(self) -> None:
        """Ligne 542 : enregistrement niveau 0 vide lève ConversionError."""
        importer = GEDCOMImporter()
        with pytest.raises(ConversionError, match="vide"):
            importer._parse_line("0", 1)

    def test_parse_line_no_tag_non_zero(self) -> None:
        """Ligne 552 : ligne non-niveau-0 sans balise lève ConversionError."""
        importer = GEDCOMImporter()
        with pytest.raises(ConversionError, match="sans balise"):
            importer._parse_line("1", 1)

    # ---- import_from_string INDI/FAM sans xref ----

    def test_import_indi_without_xref_skipped(self) -> None:
        """Ligne 431 : INDI sans xref ignoré (résultat vide)."""
        importer = GEDCOMImporter()
        ged = "0 HEAD\n1 CHAR UTF-8\n0 INDI\n1 NAME\n2 GIVN A\n0 TRLR\n"
        genealogy = importer.import_from_string(ged)
        assert len(genealogy.persons) == 0

    def test_import_fam_without_xref_skipped(self) -> None:
        """Ligne 436 : FAM sans xref ignoré."""
        importer = GEDCOMImporter()
        ged = "0 HEAD\n0 FAM\n1 HUSB @I1@\n0 TRLR\n"
        genealogy = importer.import_from_string(ged)
        assert len(genealogy.families) == 0

    # ---- _apply_head_block ----

    def test_apply_head_block_char_and_sour(self) -> None:
        """Lignes 570-577 : CHAR et SOUR dans HEAD."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
1 CHAR UTF-8
1 SOUR MyApp
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        assert genealogy.metadata.encoding == "UTF-8"
        assert any("SOUR MyApp" in note for note in genealogy.metadata.database_notes)

    # ---- _parse_gedcom_date ----

    def test_parse_gedcom_date_empty(self) -> None:
        """Ligne 581 : chaîne vide retourne None."""
        importer = GEDCOMImporter()
        assert importer._parse_gedcom_date("", 1) is None
        assert importer._parse_gedcom_date("   ", 1) is None

    def test_parse_gedcom_date_prefix_only(self) -> None:
        """Ligne 600 : préfixe seul retourne None."""
        importer = GEDCOMImporter()
        assert importer._parse_gedcom_date("ABT", 1) is None

    def test_parse_gedcom_date_bet(self) -> None:
        """Ligne 602 : BET retourne None (non supporté)."""
        importer = GEDCOMImporter()
        assert importer._parse_gedcom_date("BET 1900 AND 1910", 1) is None

    def test_parse_gedcom_date_year_only(self) -> None:
        """Lignes 607-608 : année seule."""
        importer = GEDCOMImporter()
        d = importer._parse_gedcom_date("1950", 1)
        assert d is not None
        assert d.year == 1950

    def test_parse_gedcom_date_month_year(self) -> None:
        """Lignes 610-613 : mois + année."""
        importer = GEDCOMImporter()
        d = importer._parse_gedcom_date("MAR 1950", 1)
        assert d is not None
        assert d.month == 3
        assert d.year == 1950

    def test_parse_gedcom_date_two_digits(self) -> None:
        """Lignes 614-616 : deux nombres (jour + mois)."""
        importer = GEDCOMImporter()
        d = importer._parse_gedcom_date("15 3", 1)
        assert d is not None
        assert d.day == 15
        assert d.month == 3

    def test_parse_gedcom_date_with_prefix(self) -> None:
        """Lignes 597-598 : préfixe ABT."""
        importer = GEDCOMImporter()
        d = importer._parse_gedcom_date("ABT 1950", 1)
        assert d is not None
        assert d.prefix == DatePrefix.ABOUT

    # ---- _parse_note_payload ----

    def test_parse_note_payload_cont_conc(self) -> None:
        """Lignes 649-656 : CONT et CONC assembles la note."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Jean
2 SURN DUPONT
1 NOTE Première ligne
2 CONT Suite ligne
2 CONC Fin
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        p = genealogy.find_person("DUPONT", "Jean", 0)
        assert p is not None
        combined = " ".join(p.notes)
        assert "Première ligne" in combined
        assert "Suite ligne" in combined
        assert "Fin" in combined

    # ---- _slash_name_parts ----

    def test_slash_name_parts_format(self) -> None:
        """Lignes 678-684 : format /NOM/ Prénom."""
        importer = GEDCOMImporter()
        last, first = importer._slash_name_parts("Jean /DUPONT/")
        assert last == "DUPONT"
        assert first == "Jean"

    def test_import_indi_slash_name_fallback(self) -> None:
        """Lignes 775-779 : NAME avec valeur slash quand GIVN/SURN absents."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME Jean /DUPONT/
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        assert len(genealogy.persons) == 1
        p = next(iter(genealogy.persons.values()))
        assert p.last_name == "DUPONT"
        assert p.first_name == "Jean"

    # ---- _import_indi_block : niveaux > 1, SEX, DEAT, NOTE, FAMS, FAMC, TITL, OCCU ----

    def test_import_indi_level_not_one_skipped(self) -> None:
        """Lignes 766-767 : lignes niveau != 1 ignorées."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Jean
2 SURN DUPONT
3 SOME_SUB_TAG ignored
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        assert len(genealogy.persons) == 1

    def test_import_indi_sex_unknown(self) -> None:
        """Ligne 788 : SEX inconnu."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Alex
2 SURN MARTIN
1 SEX U
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        p = genealogy.find_person("MARTIN", "Alex", 0)
        assert p is not None
        assert p.gender == Gender.UNKNOWN

    def test_import_indi_death_fields(self) -> None:
        """Lignes 800-806 : DEAT avec date et lieu."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Paul
2 SURN BLANC
1 DEAT
2 DATE 25 DEC 2020
2 PLAC Paris
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        p = genealogy.find_person("BLANC", "Paul", 0)
        assert p is not None
        assert p.death_date is not None
        assert p.death_date.year == 2020
        assert p.death_place == "Paris"

    def test_import_indi_note(self) -> None:
        """Lignes 809-814 : NOTE au niveau INDI."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Claude
2 SURN RENARD
1 NOTE Une remarque importante
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        p = genealogy.find_person("RENARD", "Claude", 0)
        assert p is not None
        assert any("remarque" in n for n in p.notes)

    def test_import_indi_titl_occu(self) -> None:
        """Lignes 823-830 : TITL et OCCU."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Emma
2 SURN LEROY
1 TITL Professeur
1 OCCU Enseignante
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        p = genealogy.find_person("LEROY", "Emma", 0)
        assert p is not None
        assert any(t.name == "Professeur" for t in p.titles)
        assert p.occupation == "Enseignante"

    def test_import_indi_fams_famc(self) -> None:
        """Lignes 815-822 : FAMS et FAMC stockés dans pending."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Lucas
2 SURN MOREAU
1 FAMS @F1@
1 FAMC @F2@
0 @F1@ FAM
0 @F2@ FAM
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        p = genealogy.find_person("MOREAU", "Lucas", 0)
        assert p is not None

    def test_import_indi_immigration_event(self) -> None:
        """Lignes 835-836 : IMMI/EMIG stockent gedcom_tag dans metadata."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Hugo
2 SURN SIMON
1 IMMI
2 DATE 1900
2 PLAC France
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        p = genealogy.find_person("SIMON", "Hugo", 0)
        assert p is not None
        assert len(p.events) == 1
        assert p.events[0].metadata.get("gedcom_tag") == "IMMI"

    def test_allocate_person_collision(self) -> None:
        """Ligne 732 : _allocate_person incrémente occurrence_number si collision."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Pierre
2 SURN DUVAL
0 @I2@ INDI
1 NAME
2 GIVN Pierre
2 SURN DUVAL
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        assert len(genealogy.persons) == 2

    # ---- _resolve_person_pointer ----

    def test_resolve_person_pointer_via_xref(self) -> None:
        """Ligne 872 : résolution via _xref_to_uid."""
        importer = GEDCOMImporter()
        genealogy = Genealogy()
        p = Person(last_name="DUPONT", first_name="Jean")
        genealogy.add_person(p)
        importer._xref_to_uid["I1"] = p.unique_id
        result = importer._resolve_person_pointer("@I1@", genealogy)
        assert result == p.unique_id

    def test_resolve_person_pointer_via_direct_uid(self) -> None:
        """Ligne 874 : résolution directe via genealogy.persons."""
        importer = GEDCOMImporter()
        genealogy = Genealogy()
        p = Person(last_name="DUPONT", first_name="Jean")
        genealogy.add_person(p)
        result = importer._resolve_person_pointer(p.unique_id, genealogy)
        assert result == p.unique_id

    # ---- _import_fam_block : MARR, DIV, NOTE, duplicate ----

    def test_import_fam_with_marriage(self) -> None:
        """Lignes 920-935 : MARR dans FAM."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Henri
2 SURN PETIT
1 SEX M
0 @I2@ INDI
1 NAME
2 GIVN Anne
2 SURN GRAND
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 15 JUN 1980
2 PLAC Lyon
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        assert len(genealogy.families) == 1
        fam = next(iter(genealogy.families.values()))
        assert fam.marriage_date is not None
        assert fam.marriage_date.year == 1980
        assert fam.marriage_place == "Lyon"

    def test_import_fam_with_divorce(self) -> None:
        """Lignes 936-950 : DIV dans FAM."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Marc
2 SURN LEFEBVRE
1 SEX M
0 @I2@ INDI
1 NAME
2 GIVN Julie
2 SURN THOMAS
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 DIV
2 DATE 2005
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        fam = next(iter(genealogy.families.values()))
        assert fam.divorce_date is not None
        assert fam.divorce_date.year == 2005

    def test_import_fam_note(self) -> None:
        """Lignes 950-955 : NOTE dans FAM."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @F1@ FAM
1 NOTE Remarque sur la famille
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        fam = next(iter(genealogy.families.values()))
        assert any("Remarque" in c for c in fam.comments)

    def test_import_fam_duplicate_raises(self) -> None:
        """Lignes 885-886 : FAM dupliqué lève ConversionError."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @F1@ FAM
0 @F1@ FAM
0 TRLR
"""
        with pytest.raises(ConversionError, match="dupliquée"):
            importer.import_from_string(ged)

    def test_import_fam_non_level1_lines_skipped(self) -> None:
        """Lignes 905-906 : lignes niveau != 1 dans FAM ignorées."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @F1@ FAM
2 SOME_TAG ignored
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        assert len(genealogy.families) == 1

    # ---- _resolve_family_pointers ----

    def test_resolve_family_pointers_fams_and_famc(self) -> None:
        """Lignes 975-989 : résolution des pointeurs FAMS/FAMC après import."""
        importer = GEDCOMImporter()
        ged = """0 HEAD
0 @I1@ INDI
1 NAME
2 GIVN Pere
2 SURN MARTIN
1 SEX M
1 FAMS @F1@
0 @I2@ INDI
1 NAME
2 GIVN Enfant
2 SURN MARTIN
1 SEX M
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I2@
0 TRLR
"""
        genealogy = importer.import_from_string(ged)
        pere = genealogy.find_person("MARTIN", "Pere", 0)
        enfant = genealogy.find_person("MARTIN", "Enfant", 0)
        assert pere is not None
        assert enfant is not None
        assert len(pere.families_as_spouse) == 1
        assert len(enfant.families_as_child) == 1
