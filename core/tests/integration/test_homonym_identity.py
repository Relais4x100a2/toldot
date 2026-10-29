"""Homonymes GeneWeb : « NOM Prénom » + numéro d'occurrence = identité unique."""

from pathlib import Path

import pytest

from geneweb_py import GeneWebParser

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample_tree.gw"


@pytest.mark.parametrize("use_multipass", [False, True])
def test_homonyms_are_distinct_persons(use_multipass):
    genealogy = GeneWebParser(use_multipass=use_multipass).parse_file(str(FIXTURE))

    jeans = [
        p
        for p in genealogy.persons.values()
        if (p.last_name, p.first_name) == ("DUPONT", "Jean")
    ]
    assert sorted(p.occurrence_number for p in jeans) == [0, 1]
    assert len(genealogy.persons) == len(set(genealogy.persons))
    assert "DUPONT_Jean_1" in genealogy.persons
