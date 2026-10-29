"""R13 : une ligne de texte nu dans un bloc pevt n'est jamais jetée."""

from geneweb_py import GeneWebParser


def _evts(texte: str):
    g = GeneWebParser(validate=False).parse_string(texte)
    return g.persons["MARTIN_Jean_0"].events


def test_texte_nu_entre_deux_temoins_est_conserve():
    evts = _evts(
        "pevt MARTIN Jean\n#birt 1712\nwit m: LEROY Paul\n"
        "Parrain venu de Chartres\nwit f: LEROY Anne\nend pevt\n"
    )
    assert any("Parrain venu de Chartres" in n for e in evts for n in e.notes)


def test_texte_nu_apres_note_prolonge_la_note():
    evts = _evts(
        "pevt MARTIN Jean\n#birt 1712\nnote Premiere ligne\n"
        "Suite de la note\nend pevt\n"
    )
    assert [n for e in evts for n in e.notes] == ["Premiere ligne\nSuite de la note"]


def test_fin_de_bloc_englobe_le_texte_nu():
    evts = _evts("pevt MARTIN Jean\n#birt 1712\nSuite\nend pevt\n")
    assert evts[0].end_line == 3


def test_texte_nu_dans_bloc_fam_est_conserve():
    g = GeneWebParser(validate=False).parse_string(
        "fam MARTIN Pierre +1705 DUBOIS Marie\nwit m: LEROY Paul\n"
        "Mariage celebre a Dreux\ncomm Un commentaire\nbeg\n- h Jean 1712\nend\n"
    )
    (fam,) = g.families.values()
    assert any("Mariage celebre a Dreux" in c for c in fam.comments)
