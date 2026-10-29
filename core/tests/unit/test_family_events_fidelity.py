"""Fidélité du parsing des témoins #offi, des sources fevt et du divorce de la ligne fam.

Données synthétiques uniquement.
"""

from geneweb_py import GeneWebParser
from geneweb_py.core.event import WitnessKind


def _parse(texte: str):  # type: ignore[no-untyped-def]
    return GeneWebParser(validate=False).parse_string(texte)


FEVT = """\
fam DUPONT Paul +1750 #mp Chartres MARTIN Anne
fevt
#marr 12/5/1750 #p Chartres #s Registre BMS Chartres
wit m: #offi BERNARD Henri
wit f: #godp LEROY Jeanne
end fevt
"""


def test_fevt_source_multi_mots_est_complete() -> None:
    (famille,) = _parse(FEVT).families.values()
    assert famille.events[0].source == "Registre BMS Chartres"


def test_fevt_temoin_offi_est_conserve() -> None:
    (famille,) = _parse(FEVT).families.values()
    temoins = famille.events[0].witnesses
    assert [(t["person_id"], t["witness_kind"]) for t in temoins] == [
        ("BERNARD_Henri_0", WitnessKind.OFFICER),
        ("LEROY_Jeanne_0", WitnessKind.GODPARENT),
    ]


def test_pevt_temoin_offi_est_conserve() -> None:
    g = _parse(
        "pevt DUPONT Luc\n#bapt 3/3/1712\nwit m: #offi BERNARD Henri\nend pevt\n"
    )
    evt = g.persons["DUPONT_Luc_0"].events[0]
    assert [(t["person_id"], t["witness_kind"]) for t in evt.witnesses] == [
        ("BERNARD_Henri_0", WitnessKind.OFFICER)
    ]


def test_fevt_borne_de_fin_inclut_end_fevt() -> None:
    (famille,) = _parse(FEVT).families.values()
    assert (famille.events[0].start_line, famille.events[0].end_line) == (3, 5)


def test_divorce_de_la_ligne_fam_est_lu() -> None:
    (famille,) = _parse("fam DUPONT Paul +1750 - 1760 MARTIN Anne\n").families.values()
    assert famille.divorce_date is not None
    assert famille.divorce_date.year == 1760


def test_tiret_d_une_source_n_est_pas_un_divorce() -> None:
    texte = (
        "fam DUPONT Paul +1750 #mp Chartres MARTIN Anne\n"
        "src BMS Chartres 1750-1760\n"
        "beg\n- h Luc\nend\n"
    )
    (famille,) = _parse(texte).families.values()
    assert famille.divorce_date is None
    assert famille.marriage_status.name == "MARRIED"
    assert famille.family_source == "BMS Chartres 1750-1760"


def test_divorce_apres_lieu_de_mariage() -> None:
    texte = "fam DUPONT Paul +1750 #mp Chartres - 1760 MARTIN Anne\n"
    (famille,) = _parse(texte).families.values()
    assert famille.divorce_date is not None and famille.divorce_date.year == 1760
    assert famille.wife_id == "MARTIN_Anne_0"
