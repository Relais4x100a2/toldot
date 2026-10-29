"""``Date.to_bounds`` : intervalle grégorien [date_min, date_max] (modèle §5.6)."""

from datetime import date

import pytest

from geneweb_py.core.date import Date
from geneweb_py.core.exceptions import GeneWebError, UnsupportedCalendarError


def bounds(text: str, **kwargs: int):  # type: ignore[no-untyped-def]
    return Date.parse(text).to_bounds(**kwargs)


def test_exact_day() -> None:
    assert bounds("3/3/1712") == (date(1712, 3, 3), date(1712, 3, 3))


def test_year_only_spans_the_whole_year() -> None:
    assert bounds("1712") == (date(1712, 1, 1), date(1712, 12, 31))


def test_month_only_spans_the_month_including_leap_february() -> None:
    assert bounds("2/1712") == (date(1712, 2, 1), date(1712, 2, 29))


def test_about_widens_by_default_window_of_five_years() -> None:
    assert bounds("~1712") == (date(1707, 1, 1), date(1717, 12, 31))


def test_about_window_is_configurable() -> None:
    assert bounds("~3/3/1712", fuzzy_window_years=2) == (
        date(1710, 3, 3),
        date(1714, 3, 3),
    )


def test_about_on_leap_day_falls_back_to_feb_28() -> None:
    assert bounds("~29/2/1712", fuzzy_window_years=1) == (
        date(1711, 2, 28),
        date(1713, 2, 28),
    )


def test_maybe_keeps_the_declared_precision() -> None:
    assert bounds("?1712") == (date(1712, 1, 1), date(1712, 12, 31))


def test_before_is_open_below_and_stops_the_day_before() -> None:
    assert bounds("<1712") == (None, date(1711, 12, 31))


def test_after_is_open_above_and_starts_the_day_after() -> None:
    assert bounds(">1712") == (date(1713, 1, 1), None)
    assert bounds(">3/3/1712") == (date(1712, 3, 4), None)


def test_or_covers_all_alternatives() -> None:
    assert bounds("1712|1713") == (date(1712, 1, 1), date(1713, 12, 31))


def test_between_covers_both_years() -> None:
    assert bounds("1710..1715") == (date(1710, 1, 1), date(1715, 12, 31))


@pytest.mark.parametrize("text", ["0", "0(Pâques 1712)"])
def test_unknown_and_free_text_dates_have_no_bounds(text: str) -> None:
    assert bounds(text) == (None, None)


def test_julian_day_is_converted_to_gregorian() -> None:
    assert bounds("12/3/1712J") == (date(1712, 3, 23), date(1712, 3, 23))


def test_julian_conversion_follows_the_century_offsets() -> None:
    assert bounds("1/1/1500J")[0] == date(1500, 1, 10)  # écart de 9 jours
    assert bounds("28/2/1700J")[0] == date(1700, 3, 10)  # écart de 10 jours
    assert bounds("29/2/1700J")[0] == date(1700, 3, 11)  # 1700 julien est bissextile


def test_julian_year_only_converts_each_bound() -> None:
    assert bounds("1712J") == (date(1712, 1, 12), date(1713, 1, 11))


@pytest.mark.parametrize("text", ["5/3/1790F", "1/1/5500H"])
def test_republican_and_hebrew_calendars_are_refused(text: str) -> None:
    with pytest.raises(UnsupportedCalendarError, match="calendrier"):
        bounds(text)


def test_unsupported_calendar_error_is_a_geneweb_error() -> None:
    assert issubclass(UnsupportedCalendarError, GeneWebError)
