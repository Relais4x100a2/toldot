"""``Date.raw_text`` conserve la date telle qu'écrite dans le ``.gw`` (R13)."""

import pytest

from geneweb_py import GeneWebParser
from geneweb_py.core.date import Date


@pytest.mark.parametrize(
    "ecrit", ["3/3/1712", "~1712", "?1750", "<1800", "1700..1710", "0(5_Mai_1990)"]
)
def test_parse_conserve_la_chaine_d_origine(ecrit: str) -> None:
    assert Date.parse(ecrit).raw_text == ecrit


def test_parse_with_fallback_conserve_aussi_une_date_illisible() -> None:
    assert Date.parse_with_fallback("n'importe quoi").raw_text == "n'importe quoi"


def test_date_construite_a_la_main_n_a_pas_de_texte() -> None:
    assert Date(year=1712).raw_text is None


def test_raw_text_ne_change_pas_l_egalite() -> None:
    assert Date.parse("~1712") == Date.parse(" ~1712 ")


def test_date_d_un_evenement_garde_son_texte() -> None:
    g = GeneWebParser(validate=False).parse_string(
        "pevt DUPONT Luc\n#bapt 3/3/1712\nend pevt\n"
    )
    assert g.persons["DUPONT_Luc_0"].events[0].date.raw_text == "3/3/1712"
