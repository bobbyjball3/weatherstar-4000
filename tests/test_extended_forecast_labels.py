"""Tests for the Extended Forecast weekday column labels."""

import datetime

import pygame

from weatherstar_4000.context import AppContext, DataRegistry
from weatherstar_4000.datasources.noaa import ForecastPeriod
from weatherstar_4000.themes import CLASSIC_THEME


def _period(**kw):
    return ForecastPeriod(**kw)


def test_extended_forecast_weekday_from_start_time():
    from weatherstar_4000.screens.extended_forecast import ExtendedForecastScreen

    screen = ExtendedForecastScreen.model_validate({})
    assert screen._weekday_abbrev(_period(start_time=datetime.datetime(2026, 9, 5, 18))) == "SAT"
    assert screen._weekday_abbrev(_period(start_time=datetime.datetime(2026, 9, 6, 18))) == "SUN"
    assert screen._weekday_abbrev(_period(start_time=datetime.datetime(2026, 9, 7, 18))) == "MON"


def test_extended_forecast_weekday_from_name_when_no_start_time():
    from weatherstar_4000.screens.extended_forecast import ExtendedForecastScreen

    screen = ExtendedForecastScreen.model_validate({})
    assert screen._weekday_abbrev(_period(name="Saturday")) == "SAT"
    assert screen._weekday_abbrev(_period(name="This Afternoon")) != "THI"


def test_extended_forecast_day_label_prefers_daytime_period():
    from weatherstar_4000.screens.extended_forecast import ExtendedForecastScreen

    screen = ExtendedForecastScreen.model_validate({})
    day = _period(name="Sunday", is_daytime=True, start_time=datetime.datetime(2026, 9, 6, 18))
    night = _period(
        name="Saturday Night", is_daytime=False, start_time=datetime.datetime(2026, 9, 5)
    )
    assert screen._day_label(day, night) == "SUN"
    # If the pair opens at night (forecast begins overnight), label the next day.
    assert screen._day_label(night, day) == "SUN"


def test_extended_forecast_renders(fonts):
    from weatherstar_4000.screens.extended_forecast import ExtendedForecastScreen

    screen = ExtendedForecastScreen.model_validate({})
    surface = pygame.Surface((640, 480))

    class _Weather:
        def get_forecast(self, lat, lon, units="us"):
            return []

    data = DataRegistry()
    data.register("weather", _Weather())
    ctx = AppContext(theme=CLASSIC_THEME, fonts=fonts, data=data)
    # Without data the screen draws its "NO DATA" message without raising.
    screen.draw(surface, ctx, 1 / 30)
