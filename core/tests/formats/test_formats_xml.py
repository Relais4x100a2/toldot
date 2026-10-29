"""
Tests formats XML (chemin backlog).

Les scénarios détaillés sont dans ``tests/unit/test_xml_format_support.py``.
"""

from geneweb_py.core.date import Date
from geneweb_py.core.event import EventType, FamilyEvent, FamilyEventType
from geneweb_py.core.family import Family
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.person import Gender, Person
from geneweb_py.formats.xml import XMLExporter, XMLImporter


def test_formats_xml_roundtrip_person_family_event() -> None:
    """Export XML puis import : Person, Family et événement familial."""
    genealogy = Genealogy()
    husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
    wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
    genealogy.add_person(husband)
    genealogy.add_person(wife)

    family = Family(
        family_id="fam_rt_formats",
        husband_id=husband.unique_id,
        wife_id=wife.unique_id,
        marriage_date=Date(year=2000, month=5, day=1),
        marriage_place="Lyon",
    )
    family.add_witness("Temoin_A", "m")
    family.add_event(
        FamilyEvent(
            event_type=EventType.MARRIAGE,
            family_event_type=FamilyEventType.MARRIAGE,
            date=Date(year=2000, month=5, day=1),
            place="Lyon",
            notes=["convocation"],
        )
    )
    genealogy.add_family(family)

    xml_string = XMLExporter().export_to_string(genealogy)
    imported = XMLImporter().import_from_string(xml_string)

    assert len(imported.persons) == 2
    assert len(imported.families) == 1
    assert imported.find_person_by_id(husband.unique_id) is not None
    assert imported.find_person_by_id(wife.unique_id) is not None
    fam = list(imported.families.values())[0]
    assert fam.family_id == "fam_rt_formats"
    assert fam.husband_id == husband.unique_id
    assert fam.wife_id == wife.unique_id
    assert fam.marriage_place == "Lyon"
    assert len(fam.witnesses) == 1
    assert fam.witnesses[0]["person_id"] == "Temoin_A"
    assert len(fam.events) == 1
    assert fam.events[0].family_event_type == FamilyEventType.MARRIAGE
    assert fam.events[0].notes == ["convocation"]
