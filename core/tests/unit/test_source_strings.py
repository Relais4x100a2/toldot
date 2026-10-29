"""Les chaînes de source doivent être restituées telles qu'écrites."""

from pathlib import Path

import pytest

from geneweb_py import GeneWebParser

FIXTURE = Path(__file__).parent.parent / "fixtures" / "chronologia_sample_5_7.gw"


@pytest.fixture(scope="module")
def genealogy():
    return GeneWebParser(validate=False).parse_file(FIXTURE)


def test_pevt_source_keeps_spaces(genealogy):
    jean = genealogy.persons["MARTIN_Jean_0"]
    bapt = next(e for e in jean.events if e.event_type.name == "BAPTISM")
    assert bapt.source == "BMS Saint-Aubin f°42v"


def test_family_src_line_keeps_all_words(genealogy):
    family = next(iter(genealogy.families.values()))
    assert family.family_source == "BMS Saint-Aubin 1705-1715"


def test_source_url_stays_contiguous():
    text = (
        "fam DUPONT Paul + MARTIN Anne\n"
        "src https://example.org/acte?id=1\n"
        "beg\n- h Luc\nend\n"
    )
    family = next(
        iter(GeneWebParser(validate=False).parse_string(text).families.values())
    )
    assert family.family_source == "https://example.org/acte?id=1"
