"""Intervalles complets (``j/m/a..j/m/a``) et calendrier républicain (``...F``)."""

from datetime import date

import pytest

from geneweb_py.core.date import Date, DatePrefix
from geneweb_py.core.exceptions import UnsupportedCalendarError


def test_intervalle_complet_garde_les_deux_dates():
    d = Date.parse_with_fallback("12/3/1710..15/4/1715")
    assert not d.is_unknown
    assert d.prefix == DatePrefix.BETWEEN
    assert (d.alternative_dates[0].day, d.alternative_dates[0].month) == (15, 4)
    assert d.to_bounds() == (date(1710, 3, 12), date(1715, 4, 15))
    assert d.raw_text == "12/3/1710..15/4/1715"


def test_intervalle_annee_vers_date_complete():
    d = Date.parse_with_fallback("1710..15/4/1715")
    assert d.to_bounds() == (date(1710, 1, 1), date(1715, 4, 15))


def test_intervalle_annees_inchange():
    d = Date.parse_with_fallback("1710..1715")
    assert d.to_bounds() == (date(1710, 1, 1), date(1715, 12, 31))


def test_intervalle_complet_se_reaffiche_avec_les_deux_bornes():
    assert str(Date.parse("12/3/1710..15/4/1715")).endswith("..15/04/1715")


@pytest.mark.parametrize(
    "texte,attendu",
    [
        ("1/1/1F", (date(1792, 9, 22),) * 2),
        ("18/2/8F", (date(1799, 11, 9),) * 2),  # 18 brumaire an VIII
        ("28/8/12F", (date(1804, 5, 18),) * 2),  # 28 floréal an XII
        ("13/1/4F", (date(1795, 10, 5),) * 2),  # 13 vendémiaire an IV
        ("5/13/3F", (date(1795, 9, 21),) * 2),  # an III sextile : dernier jour
        ("6/13/3F", (date(1795, 9, 22),) * 2),
        ("2/1/8F", None),
    ],
)
def test_jour_republicain_converti_en_gregorien(texte, attendu):
    d = Date.parse(texte)
    if attendu is None:
        attendu = (date(1799, 9, 24),) * 2
    assert d.to_bounds() == attendu


def test_mois_et_annee_republicains_couvrent_leur_periode():
    assert Date.parse("1/8F").to_bounds() == (date(1799, 9, 23), date(1799, 10, 22))
    assert Date.parse("8F").to_bounds() == (date(1799, 9, 23), date(1800, 9, 22))
    assert Date.parse("14F").to_bounds() == (date(1805, 9, 23), date(1805, 12, 31))


def test_intervalle_republicain_herite_du_calendrier():
    d = Date.parse("1/1/1F..1/1/2F")
    assert d.to_bounds() == (date(1792, 9, 22), date(1793, 9, 22))


def test_prefixe_republicain_s_applique_aux_bornes_gregoriennes():
    d = Date.parse(">18/2/8F")
    assert d.to_bounds() == (date(1799, 11, 10), None)


def test_annee_republicaine_hors_periode_reste_non_supportee():
    with pytest.raises(UnsupportedCalendarError):
        Date.parse("1/1/15F").to_bounds()


def test_jour_complementaire_impossible_est_refuse():
    with pytest.raises(ValueError):
        Date.parse("6/13/2F").to_bounds()  # an II non sextile : 5 jours


def test_mois_treize_refuse_hors_calendrier_republicain():
    with pytest.raises(ValueError):
        Date.parse("1/13/1700")


def test_calendrier_hebreu_reste_non_supporte():
    with pytest.raises(UnsupportedCalendarError):
        Date.parse("1/1/5000H").to_bounds()
