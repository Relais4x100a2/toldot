"""Provenance : start_line / end_line sur Person, Family et Event."""

from pathlib import Path

import pytest

from geneweb_py import GeneWebParser
from geneweb_py.core.event import EventType

FIXTURE = Path(__file__).parent.parent / "fixtures" / "chronologia_sample_5_7.gw"


def _parse(streaming: bool = False):
    parser = GeneWebParser(validate=False)
    if streaming:
        return parser._parse_file_streaming(FIXTURE)
    return parser.parse_file(FIXTURE)


@pytest.fixture(params=[False, True], ids=["normal", "streaming"])
def genealogy(request):
    return _parse(streaming=request.param)


def _person(genealogy, last, first):
    return next(
        p
        for p in genealogy.persons.values()
        if p.last_name == last and p.first_name == first
    )


def test_family_spans_fam_line_to_end_of_block(genealogy):
    family = next(iter(genealogy.families.values()))
    assert (family.start_line, family.end_line) == (4, 8)


def test_event_spans_tag_line_to_last_witness(genealogy):
    jean = _person(genealogy, "MARTIN", "Jean")
    bapt = next(e for e in jean.events if e.event_type == EventType.BAPTISM)
    assert (bapt.start_line, bapt.end_line) == (11, 15)


def test_single_line_event_has_equal_bounds(genealogy):
    jean = _person(genealogy, "MARTIN", "Jean")
    death = next(e for e in jean.events if e.event_type == EventType.DEATH)
    assert (death.start_line, death.end_line) == (19, 19)


def test_person_takes_first_defining_block(genealogy):
    assert _person(genealogy, "MARTIN", "Pierre").start_line == 4
    assert _person(genealogy, "MARTIN", "Jean").start_line == 7


def test_mentions_do_not_define_person(genealogy):
    girard = _person(genealogy, "GIRARD", "Camille")
    assert girard.start_line is None
    assert girard.end_line is None


def test_person_not_overwritten_by_later_pevt(genealogy):
    jean = _person(genealogy, "MARTIN", "Jean")
    assert (jean.start_line, jean.end_line) == (7, 7)


def test_default_is_none():
    from geneweb_py.core.event import Event, EventType
    from geneweb_py.core.family import Family
    from geneweb_py.core.person import Person

    assert Event(event_type=EventType.BIRTH).start_line is None
    assert Family(family_id="F").end_line is None
    assert Person(last_name="A", first_name="B").start_line is None
