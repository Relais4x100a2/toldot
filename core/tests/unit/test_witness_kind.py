"""Témoins ``#godp`` : le rôle est conservé et aucune personne fantôme n'est créée."""

from pathlib import Path

import pytest

from geneweb_py import GeneWebParser
from geneweb_py.core.event import WitnessKind

FIXTURE = Path(__file__).parent.parent / "fixtures" / "chronologia_sample_5_7.gw"


@pytest.fixture(scope="module")
def baptism_witnesses() -> dict:
    genealogy = GeneWebParser(validate=False).parse_file(str(FIXTURE))
    jean = genealogy.persons["MARTIN_Jean_0"]
    bapt = next(e for e in jean.events if e.event_type.value == "bapt")
    return {w["person_id"]: w for w in bapt.witnesses}


def test_godparent_witness_is_attached_with_kind(baptism_witnesses: dict) -> None:
    witness = baptism_witnesses["MOREAU_Louis_0"]
    assert witness["type"] == "m"
    assert witness["witness_kind"] is WitnessKind.GODPARENT


def test_godparent_with_occurrence_keeps_occurrence(baptism_witnesses: dict) -> None:
    witness = baptism_witnesses["DUBOIS_Anne_2"]
    assert witness["type"] == "f"
    assert witness["witness_kind"] is WitnessKind.GODPARENT


def test_plain_witness_has_no_kind(baptism_witnesses: dict) -> None:
    assert baptism_witnesses["LEROY_Jean_0"]["witness_kind"] is None


def test_witness_without_sex_is_attached(baptism_witnesses: dict) -> None:
    witness = baptism_witnesses["GIRARD_Camille_0"]
    assert witness["type"] is None
    assert witness["witness_kind"] is None


def test_no_phantom_person_named_after_the_marker() -> None:
    genealogy = GeneWebParser(validate=False).parse_file(str(FIXTURE))
    assert not [k for k in genealogy.persons if "godp" in k.lower()]
