"""Tags d'événements familiaux autres que marr/div/sep/enga dans un bloc fevt."""

import pytest

from geneweb_py import GeneWebParser
from geneweb_py.core.event import FamilyEventType

_BASE = "fam MARTIN Pierre +1705 DUBOIS Marie\nfevt\n"


def _evts(corps: str):
    g = GeneWebParser(validate=False).parse_string(_BASE + corps + "end fevt\n")
    return [e for f in g.families.values() for e in f.events]


@pytest.mark.parametrize(
    "tag,attendu",
    [
        ("marc", FamilyEventType.MARRIAGE_CONTRACT),
        ("marb", FamilyEventType.MARRIAGE_BANN),
        ("marl", FamilyEventType.MARRIAGE_LICENSE),
        ("nmar", FamilyEventType.NO_MARRIAGE),
        ("nmen", FamilyEventType.NO_MENTION),
        ("anul", FamilyEventType.ANNULMENT),
        ("pacs", FamilyEventType.PACS),
        ("resi", FamilyEventType.RESIDENCE),
    ],
)
def test_tag_familial_standard_devient_un_evenement_complet(tag, attendu):
    (e,) = _evts(
        f"#{tag} 1704 #p Lyon #s Reg\nwit m: LEROY Paul\nwnote tel\nnote une note\n"
    )
    assert e.family_event_type == attendu
    assert str(e.date) == "1704"
    assert e.place == "Lyon"
    assert e.source == "Reg"
    assert len(e.witnesses) == 1 and e.witnesses[0]["note"] == "tel"
    assert e.notes == ["une note"]


def test_tag_personnalise_est_capture_en_type_libre():
    (e,) = _evts("#Hypotheque 1704 #p Lyon\n")
    assert e.family_event_type == FamilyEventType.OTHER
    assert e.event_type_raw == "Hypotheque"
    assert str(e.date) == "1704" and e.place == "Lyon"


def test_evenements_standard_et_autres_gardent_l_ordre_du_bloc():
    evts = _evts("#marc 1704\n#marr 1705\n#resi 1706\n")
    assert [e.family_event_type for e in evts] == [
        FamilyEventType.MARRIAGE_CONTRACT,
        FamilyEventType.MARRIAGE,
        FamilyEventType.RESIDENCE,
    ]
