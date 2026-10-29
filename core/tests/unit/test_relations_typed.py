"""Blocs ``rel`` : relations typées, occurrences préservées, rien d'aplati en note."""

from pathlib import Path

import pytest

from geneweb_py import GeneWebParser
from geneweb_py.core.person import ParentRole, Relation, RelationType

FIXTURE = Path(__file__).parent.parent / "fixtures" / "chronologia_sample_5_7.gw"


@pytest.fixture(scope="module")
def genealogy():  # type: ignore[no-untyped-def]
    return GeneWebParser(validate=False).parse_file(str(FIXTURE))


def test_rel_block_yields_typed_relations(genealogy) -> None:  # type: ignore[no-untyped-def]
    jean = genealogy.persons["MARTIN_Jean_0"]
    assert jean.relation_links == [
        Relation(RelationType.GODPARENT, ParentRole.FATHER, "MOREAU_Louis_1"),
        Relation(RelationType.GODPARENT, ParentRole.MOTHER, "DUBOIS_Anne_2"),
        Relation(RelationType.ADOPTION, None, "LEROY_Jean_3"),
        Relation(RelationType.FOSTER, ParentRole.MOTHER, "GIRARD_Camille_0"),
    ]


def test_relation_targets_keep_their_occurrence(genealogy) -> None:  # type: ignore[no-untyped-def]
    assert "LEROY_Jean_3" in genealogy.persons
    # l'homonyme LEROY Jean.0 (témoin) reste une autre personne
    assert "LEROY_Jean_0" in genealogy.persons
    assert genealogy.persons["LEROY_Jean_3"].occurrence_number == 3


def test_relations_are_not_flattened_into_notes(genealogy) -> None:  # type: ignore[no-untyped-def]
    jean = genealogy.persons["MARTIN_Jean_0"]
    assert not [n for n in jean.notes if n.startswith("Relations:")]


def test_legacy_relations_dict_still_populated(genealogy) -> None:  # type: ignore[no-untyped-def]
    jean = genealogy.persons["MARTIN_Jean_0"]
    assert jean.relations["godp"] == ["MOREAU_Louis_1", "DUBOIS_Anne_2"]
    assert jean.relations["adop"] == ["LEROY_Jean_3"]


def test_rel_subject_occurrence_is_honoured(tmp_path: Path) -> None:
    gw = tmp_path / "rel_occ.gw"
    gw.write_text(
        "rel MARTIN Jean.2\nbeg\n- reco fath: DUPONT Paul.1\nend\n", encoding="utf-8"
    )
    g = GeneWebParser(validate=False).parse_file(str(gw))
    assert "MARTIN_Jean_0" not in g.persons
    assert g.persons["MARTIN_Jean_2"].relation_links == [
        Relation(RelationType.RECOGNITION, ParentRole.FATHER, "DUPONT_Paul_1")
    ]


def test_candidate_relation_type(tmp_path: Path) -> None:
    gw = tmp_path / "rel_cand.gw"
    gw.write_text(
        "rel MARTIN Jean\nbeg\n- cand moth: DUPONT Anne\nend\n", encoding="utf-8"
    )
    g = GeneWebParser(validate=False).parse_file(str(gw))
    assert g.persons["MARTIN_Jean_0"].relation_links[0].relation_type is (
        RelationType.CANDIDATE
    )
