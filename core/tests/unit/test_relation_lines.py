"""Provenance (start_line/end_line) des lignes d'un bloc ``rel``."""

from pathlib import Path

from geneweb_py import GeneWebParser

FIXTURE = Path(__file__).parents[1] / "fixtures" / "chronologia_sample_5_7.gw"
ATTENDU = {
    "MOREAU_Louis_1": 24,
    "DUBOIS_Anne_2": 25,
    "LEROY_Jean_3": 26,
    "GIRARD_Camille_0": 27,
}


def _lignes(genealogie):  # type: ignore[no-untyped-def]
    liens = genealogie.persons["MARTIN_Jean_0"].relation_links
    return {lien.target_person_key: (lien.start_line, lien.end_line) for lien in liens}


def test_chaque_ligne_rel_porte_sa_ligne() -> None:
    g = GeneWebParser(validate=False).parse_file(FIXTURE)
    assert _lignes(g) == {cle: (n, n) for cle, n in ATTENDU.items()}


def test_lignes_rel_identiques_en_streaming() -> None:
    complet = GeneWebParser(validate=False).parse_file(FIXTURE)
    flux = GeneWebParser(validate=False)._parse_file_streaming(FIXTURE)
    assert _lignes(flux) == _lignes(complet)


def test_lignes_rel_absentes_par_defaut() -> None:
    from geneweb_py.core.person import ParentRole, Relation, RelationType

    r = Relation(RelationType.ADOPTION, ParentRole.FATHER, "A_B_0")
    assert (r.start_line, r.end_line) == (None, None)
