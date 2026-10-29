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


def test_wnote_de_bloc_fam_est_conserve_sans_perte():
    g = GeneWebParser(validate=False).parse_string(
        "fam MARTIN Pierre +1705 DUBOIS Marie\nwit m: LEROY Paul\n"
        "wnote Cousin du marie\nwit f: LEROY Anne\nbeg\n- h Jean 1712\nend\n"
    )
    (fam,) = g.families.values()
    assert [w.get("note") for w in fam.witnesses] == ["Cousin du marie", None]
    assert fam.comments == [] and len(fam.children) == 1


def test_wnote_dans_fevt_est_conserve():
    g = GeneWebParser(validate=False).parse_string(
        "fam MARTIN Pierre +1705 DUBOIS Marie\nbeg\n- h Jean 1712\nend\n\n"
        "fevt MARTIN Pierre + DUBOIS Marie\n#marr 1705 #p Dreux\n"
        "wit m: LEROY Paul\nwnote Cousin du marie\nwit f: LEROY Anne\nend fevt\n"
    )
    (fam,) = g.families.values()
    (evt,) = fam.events
    assert [w.get("note") for w in evt.witnesses] == ["Cousin du marie", None]
    assert evt.notes == []


def test_texte_nu_apres_temoin_date_dans_en_tete_fam():
    g = GeneWebParser(validate=False).parse_string(
        "fam MARTIN Pierre +1705 DUBOIS Marie\nwit m: LEROY Paul 1650\n"
        "Parrain venu de Chartres\nbeg\n- h Jean 1712\nend\n"
    )
    (fam,) = g.families.values()
    assert fam.comments == ["Parrain venu de Chartres"]
    assert len(fam.children) == 1


def test_wnote_de_bloc_pevt_va_sur_le_temoin_precedent():
    evts = _evts(
        "pevt MARTIN Jean\n#bapt 1712\nwit m: LEROY Paul\n"
        "wnote Parrain venu de Chartres\nwit f: LEROY Anne\nend pevt\n"
    )
    assert [w.get("note") for w in evts[0].witnesses] == [
        "Parrain venu de Chartres",
        None,
    ]
    assert evts[0].notes == []


def _evts_fam(texte: str):
    g = GeneWebParser(validate=False).parse_string(texte)
    return [e.event_type.name for f in g.families.values() for e in f.events]


def test_fevt_commencant_par_une_note_reste_rattache_a_sa_famille():
    base = "fam MARTIN Pierre +1705 DUBOIS Marie\nfevt\n"
    assert _evts_fam(base + "note x\n#marr 1705\nend fevt\n") == ["MARRIAGE"]


def test_fevt_commencant_par_un_texte_nu_ne_cree_pas_de_personne_fantome():
    g = GeneWebParser(validate=False).parse_string(
        "fam MARTIN Pierre +1705 DUBOIS Marie\nfevt\nPrecision utile\n#marr 1705\nend fevt\n"
    )
    assert sorted(g.persons) == ["DUBOIS_Marie_0", "MARTIN_Pierre_0"]


def test_source_de_mariage_sur_la_ligne_fam_ne_devient_pas_le_nom_de_l_epouse():
    g = GeneWebParser(validate=False).parse_string(
        "fam MARTIN Pierre +1705 #mp Lyon #ms Registre DUBOIS Marie\n"
        "fevt\n#marr 1705\nend fevt\n"
    )
    assert sorted(g.persons) == ["DUBOIS_Marie_0", "MARTIN_Pierre_0"]
    assert [e.event_type.name for f in g.families.values() for e in f.events] == [
        "MARRIAGE"
    ]


def test_source_de_mariage_avec_url_contenant_des_plus_ne_casse_pas_la_ligne_fam():
    g = GeneWebParser(validate=False).parse_string(
        "fam MARTIN Pierre +1705 #mp Lyon #ms Registre_(http://a.b.c/d?e=f&g=h+i+j&k=1) DUBOIS Marie\n"
        "fevt\n#marr 1705\nend fevt\n"
    )
    assert sorted(g.persons) == ["DUBOIS_Marie_0", "MARTIN_Pierre_0"]
    assert [e.event_type.name for f in g.families.values() for e in f.events] == [
        "MARRIAGE"
    ]


def test_temoin_au_nom_compose_avec_barre_recoit_sa_wnote():
    g = GeneWebParser(validate=False).parse_string(
        "pevt MARTIN Pierre\n#birt 1700\nwit f: DU/PONT_X/Y Marie\nwnote cousine\nend pevt\n"
    )
    pierre = g.persons["MARTIN_Pierre_0"]
    temoins = pierre.events[0].witnesses
    assert len(temoins) == 1
    assert temoins[0]["note"] == "cousine"
