"""
Couverture des helpers API (`serialization`, payloads personne/famille).

Complète les tests d'intégration HTTP pour les branches utilisées par les
réponses REST enrichies (dates, listes, stats par siècle).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from geneweb_py.api.family_payload import family_to_family_schema
from geneweb_py.api.person_payload import person_to_person_schema
from geneweb_py.api.serialization import (
    century_key_from_year,
    child_to_schema,
    count_by_birth_century,
    count_event_century,
    count_marriage_century,
    date_to_api_string,
    event_sources_list,
    event_to_schema,
    event_witnesses_to_api_strings,
    family_events_breakdown,
    parse_api_date_string,
    person_source_fields,
    related_family_ids_for_person,
    stable_event_id,
    title_to_schema,
    titles_from_create_schemas,
)
from geneweb_py.core.date import Date
from geneweb_py.core.event import (
    EventType,
    FamilyEvent,
    FamilyEventType,
    PersonalEvent,
)
from geneweb_py.core.family import Family, MarriageStatus
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Gender, Person, Title


class TestParseAndDateApiString:
    """Chaînes API ↔ dates domaine."""

    def test_parse_none_and_blank(self) -> None:
        assert parse_api_date_string(None) is None
        assert parse_api_date_string("") is None
        assert parse_api_date_string("   ") is None

    def test_parse_valid_and_date_to_api_roundtrip(self) -> None:
        d = parse_api_date_string("15/03/1955")
        assert d is not None
        assert date_to_api_string(d) is not None

    def test_date_to_api_none(self) -> None:
        assert date_to_api_string(None) is None


class TestTitlesFromCreateSchemas:
    """titles_from_create_schemas avec dates optionnelles."""

    def test_empty_list(self) -> None:
        assert titles_from_create_schemas([]) == []

    def test_with_start_and_end_dates(self) -> None:
        raw = SimpleNamespace(
            name="Duc",
            title_type="nob",
            place="Paris",
            start_date="1900",
            end_date="1910",
            number=1,
            is_main=True,
        )
        titles = titles_from_create_schemas([raw])
        assert len(titles) == 1
        assert titles[0].name == "Duc"
        assert titles[0].start_date is not None
        assert titles[0].end_date is not None


class TestPersonSourceFields:
    """Agrégation des sources sur une personne."""

    def test_collects_non_empty_sources(self) -> None:
        p = Person(last_name="X", first_name="Y")
        p.birth_source = " acte "
        p.person_source = ""
        p.death_source = None
        src = person_source_fields(p)
        assert src == ["acte"]


class TestChildAndWitnessesAndSources:
    """Enfants, témoins et sources d'événements."""

    def test_child_to_schema_string(self) -> None:
        sch = child_to_schema("CHILD_1")
        assert sch.person_id == "CHILD_1"

    def test_event_witnesses_variants(self) -> None:
        assert event_witnesses_to_api_strings([" a ", "", {"person_id": "W1"}, {}]) == [
            "a",
            "W1",
        ]

    def test_event_sources_list(self) -> None:
        ev = PersonalEvent(event_type=EventType.BIRTH, source="  src  ")
        assert event_sources_list(ev) == ["src"]
        ev2 = PersonalEvent(event_type=EventType.BIRTH, source="")
        assert event_sources_list(ev2) == []


class TestStableEventIdAndEventSchema:
    """IDs stables et schéma événement."""

    def test_stable_event_id_deterministic_shape(self) -> None:
        ev = PersonalEvent(event_type=EventType.BIRTH)
        eid = stable_event_id(ev, scope="person", scope_key="P1", index=0)
        assert eid.startswith("evt_person_P1_0_")

    def test_event_to_schema_personal(self) -> None:
        ev = PersonalEvent(
            event_type=EventType.BIRTH,
            date=Date(year=2001, month=1, day=2),
            notes=["a", None],
        )
        sch = event_to_schema(ev, event_id="e1", person_id="P1", family_id=None)
        assert sch.id == "e1"
        assert sch.person_id == "P1"
        assert sch.date == "02/01/2001"

    def test_event_to_schema_family_with_family_event_type(self) -> None:
        fev = FamilyEvent(
            event_type=EventType.MARRIAGE,
            family_event_type=FamilyEventType.MARRIAGE,
            place="Lyon",
        )
        sch = event_to_schema(fev, event_id="f1", person_id=None, family_id="FAM1")
        assert sch.family_id == "FAM1"
        assert sch.event_type == FamilyEventType.MARRIAGE


class TestCenturyKeysAndCounts:
    """Siècles et agrégations stats."""

    def test_century_key_edges(self) -> None:
        assert century_key_from_year(None) == "unknown"
        assert century_key_from_year(0) == "unknown"
        assert century_key_from_year(-5) == "unknown"
        assert century_key_from_year(1955) == "20"

    def test_counts_on_minimal_genealogy(self) -> None:
        g = Genealogy()
        p = Person(last_name="A", first_name="B", gender=Gender.MALE)
        p.birth_date = Date(year=1899, month=1, day=1)
        g.persons[p.unique_id] = p
        fam = Family(
            family_id="F1",
            husband_id=p.unique_id,
            marriage_date=Date(year=1900, month=5, day=1),
        )
        fam.divorce_date = Date(year=1910, month=1, day=1)
        fev = FamilyEvent(
            event_type=EventType.MARRIAGE,
            family_event_type=FamilyEventType.MARRIAGE,
            date=Date(year=1920, month=1, day=1),
        )
        fam.events.append(fev)
        g.families["F1"] = fam

        by_birth = count_by_birth_century(g)
        assert by_birth.get("19", 0) >= 1

        by_marr = count_marriage_century(g)
        assert by_marr.get("19", 0) >= 1

        evc = count_event_century(g)
        assert sum(evc.values()) >= 1

        fb = family_events_breakdown(g)
        assert fb["with_marriage_date"] >= 1
        assert fb["with_divorce_date"] >= 1


class TestFamilyEventsBreakdownDateBranches:
    """Branches _date_has_usable_parts."""

    def test_text_date_counts_as_usable(self) -> None:
        g = Genealogy()
        f = Family(family_id="F2")
        f.marriage_date = Date(text_date="0(vers_1850)")
        g.families["F2"] = f
        fb = family_events_breakdown(g)
        assert fb["with_marriage_date"] == 1

    def test_unknown_date_not_counted(self) -> None:
        g = Genealogy()
        f = Family(family_id="F3")
        f.marriage_date = Date(is_unknown=True)
        g.families["F3"] = f
        fb = family_events_breakdown(g)
        assert fb["with_marriage_date"] == 0


class TestRelatedFamilyIdsAndTitleSchema:
    """Titres et familles liées."""

    def test_related_family_ids(self) -> None:
        p = Person(last_name="A", first_name="B")
        p.families_as_spouse = ["F10", "F11"]
        assert related_family_ids_for_person(p) == ["F10", "F11"]

    def test_title_to_schema(self) -> None:
        t = Title(
            name="Mr",
            title_type="tr",
            place="X",
            start_date=Date(year=2000, month=1, day=1),
            end_date=None,
            number=0,
            is_main=False,
        )
        sch = title_to_schema(t)
        assert sch.name == "Mr"
        assert sch.start_date == "01/01/2000"


class TestPersonPayloadEventIds:
    """Branches unique_id vs stable_event_id sur les événements."""

    def test_event_with_explicit_unique_id(self) -> None:
        p = Person(last_name="LN", first_name="FN", gender=Gender.MALE)
        ev = PersonalEvent(event_type=EventType.BAPTISM)
        object.__setattr__(ev, "unique_id", "EVT_FIXED")
        p.events.append(ev)
        schema = person_to_person_schema(p)
        assert "EVT_FIXED" in schema.events

    def test_event_without_unique_id_uses_stable_id(self) -> None:
        p = Person(last_name="LN", first_name="FN", gender=Gender.MALE)
        ev = PersonalEvent(event_type=EventType.DEATH)
        p.events.append(ev)
        schema = person_to_person_schema(p)
        assert len(schema.events) == 1
        assert schema.events[0].startswith(f"evt_person_{p.unique_id}_")


class TestFamilyPayloadSchema:
    """Schéma famille : sources, divorce_place métadonnées, événements."""

    def test_divorce_place_from_metadata(self) -> None:
        f = Family(
            family_id="FX",
            husband_id="H",
            wife_id="W",
            marriage_status=MarriageStatus.MARRIED,
            metadata={"divorce_place": "  Nice  "},
        )
        sch = family_to_family_schema(f)
        assert sch.divorce_place == "Nice"

    def test_family_event_stable_ids(self) -> None:
        f = Family(family_id="FY")
        f.family_source = " paroisse "
        fe = FamilyEvent(
            event_type=EventType.MARRIAGE,
            family_event_type=FamilyEventType.MARRIAGE,
        )
        f.events.append(fe)
        sch = family_to_family_schema(f)
        assert sch.sources == ["paroisse"]
        assert len(sch.events) == 1
        assert sch.events[0].startswith("evt_family_FY_")


class TestGenealogyServiceStatsBranches:
    """get_stats : événements typés et métadonnées."""

    def test_get_stats_includes_century_breakdowns(self) -> None:
        from geneweb_py.api.services.genealogy_service import GenealogyService

        g = Genealogy()
        p = Person(last_name="A", first_name="B", gender=Gender.MALE)
        p.birth_date = Date(year=1888, month=1, day=1)
        g.persons[p.unique_id] = p
        fam = Family(
            family_id="FSTATS",
            marriage_date=Date(year=1890, month=6, day=15),
        )
        fam.events.append(
            FamilyEvent(
                event_type=EventType.MARRIAGE,
                family_event_type=FamilyEventType.MARRIAGE,
                date=Date(year=1891, month=1, day=1),
            )
        )
        g.families["FSTATS"] = fam

        svc = GenealogyService()
        svc._genealogy = g
        stats = svc.get_stats()
        assert "persons_by_birth_century" in stats
        assert "families_by_marriage_century" in stats
        assert "events_by_century" in stats
        assert stats["personal_events"] >= 0
        assert stats["family_events"] >= 1


@pytest.fixture
def genealogy_service_with_events() -> tuple:
    """Service avec événements personnel et familial pour get_event / mise à jour."""
    from geneweb_py.api.models.event import EventUpdateSchema
    from geneweb_py.api.services.genealogy_service import GenealogyService

    g = Genealogy()
    p = Person(last_name="Z", first_name="Alice", gender=Gender.FEMALE)
    pe = PersonalEvent(event_type=EventType.BIRTH, place="Paris")
    p.events.append(pe)
    g.persons[p.unique_id] = p

    fam = Family(family_id="FUPD", husband_id=p.unique_id)
    fe = FamilyEvent(
        event_type=EventType.MARRIAGE,
        family_event_type=FamilyEventType.MARRIAGE,
        place="Lyon",
    )
    fam.events.append(fe)
    g.families["FUPD"] = fam

    svc = GenealogyService()
    svc._genealogy = g
    return svc, p, fam, EventUpdateSchema


class TestGenealogyServiceEventLifecycle:
    """Parcours get_event, update_event, delete_event (couverture service)."""

    def test_update_delete_personal_event_roundtrip(
        self, genealogy_service_with_events: tuple
    ) -> None:
        svc, person, _fam, EventUpdateSchema = genealogy_service_with_events
        eid = stable_event_id(
            person.events[0], scope="person", scope_key=person.unique_id, index=0
        )
        found = svc.get_event(eid)
        assert found is not None
        updated = svc.update_event(
            eid,
            EventUpdateSchema(place="Marseille", date=None, event_type=None),
        )
        assert updated is not None
        assert updated.place == "Marseille"
        assert svc.delete_event(eid) is True
        assert svc.get_event(eid) is None

    def test_update_family_event_event_type_mapping(
        self, genealogy_service_with_events: tuple
    ) -> None:
        svc, _p, fam, EventUpdateSchema = genealogy_service_with_events
        fe = fam.events[0]
        eid = stable_event_id(fe, scope="family", scope_key=fam.family_id, index=0)
        updated = svc.update_event(
            eid,
            EventUpdateSchema(event_type=FamilyEventType.DIVORCE),
        )
        assert updated is not None
        assert getattr(updated, "family_event_type", None) == FamilyEventType.DIVORCE
