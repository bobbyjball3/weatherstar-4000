"""Tests for the 7-Day Temperature Graph screen's day labels and bar geometry."""

import calendar
import datetime
from datetime import date, timedelta

from weatherstar.context import AppContext, DataRegistry, Location
from weatherstar.datasources.noaa import ForecastPeriod


def _period(**kw):
    return ForecastPeriod(**kw)


def _screen():
    from weatherstar.screens.temperature_graph import TemperatureGraphScreen

    return TemperatureGraphScreen.model_validate({})


def test_weekday_helpers_are_robust_to_unusable_periods():
    screen = _screen()
    # Unknown weekday/name with no fallback resolves to today.
    assert ForecastPeriod().weekday_abbrev() == calendar.day_abbr[date.today().weekday()].upper()
    # A name with no embedded weekday uses the explicit fallback date.
    assert ForecastPeriod(name="Labor Day").weekday_abbrev(fallback=date(2026, 9, 7)) == "MON"
    assert screen._column_label(_period(), None, date(2026, 9, 5)) != ""


def test_column_label_is_weekday_of_start_time_not_name_truncation():
    screen = _screen()
    # NOAA "This Afternoon" would truncate to "THI"; the label must be the
    # calendar weekday of the period's own start time instead.
    day = _period(
        name="This Afternoon", is_daytime=True, start_time=datetime.datetime(2026, 9, 5, 18)
    )
    night = _period(name="Tonight", is_daytime=False, start_time=datetime.datetime(2026, 9, 5, 23))
    assert screen._column_label(day, night, fallback=date(2026, 9, 5)) == "SAT"


def test_column_label_prefers_daytime_period_of_the_pair():
    screen = _screen()
    night = _period(
        name="Saturday Night", is_daytime=False, start_time=datetime.datetime(2026, 9, 5, 23)
    )
    day = _period(name="Sunday", is_daytime=True, start_time=datetime.datetime(2026, 9, 6, 18))
    assert screen._column_label(night, day, fallback=date(2026, 9, 6)) == "SUN"


def test_column_label_never_truncates_holiday_or_relative_names():
    screen = _screen()
    assert (
        screen._column_label(_period(name="Labor Day", is_daytime=True), None, date(2026, 9, 7))
        == "MON"
    )
    assert (
        screen._column_label(_period(name="Today", is_daytime=True), None, date(2026, 9, 5))
        == "SAT"
    )
    assert (
        screen._column_label(_period(name="Saturday", is_daytime=True), None, date(2026, 9, 5))
        == "SAT"
    )


def _ctx_with_periods(periods):
    weather = type("W", (), {"get_forecast": lambda self, lat, lon: periods})()
    data = DataRegistry()
    data.register("weather", weather)
    return AppContext(data=data, location=Location(lat=28.5383, lon=-81.3792))


def test_collect_periods_labels_follow_start_time_dates():
    screen = _screen()
    base = date(2026, 9, 5)  # a Saturday
    periods = []
    for offset in range(4):
        day = base + timedelta(days=offset)
        periods.append(
            ForecastPeriod(
                name=f"This day {offset}",
                is_daytime=True,
                start_time=datetime.datetime.combine(day, datetime.time(18)),
                temperature=90.0,
            )
        )
        periods.append(
            ForecastPeriod(
                name="Tonight",
                is_daytime=False,
                start_time=datetime.datetime.combine(day, datetime.time(23)),
                temperature=70.0,
            )
        )
    temps, labels = screen._collect_periods(_ctx_with_periods(periods))
    assert labels == ["SAT", "SUN", "MON", "TUE"]
    assert len(temps) == 4


def test_plot_band_keeps_labels_inside_the_chart_frame():
    screen = _screen()
    from weatherstar.screens import temperature_graph as m

    for text_h in (12, 16, 20, 24, 28, 32, 40):
        top, bottom, label_offset = screen._plot_band(text_h)
        assert m._GRAPH_TOP < top < bottom < m._GRAPH_TOP + m._GRAPH_HEIGHT
        # A centered number of this height clears the bar end by a gap while its
        # far edge stays inside the frame (never spilling past the axes).
        assert top - label_offset - text_h // 2 >= m._GRAPH_TOP
        assert bottom + label_offset + text_h // 2 <= m._GRAPH_TOP + m._GRAPH_HEIGHT
