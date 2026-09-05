"""Tests for the Extended Forecast weekday column labels."""

import pygame

from weatherstar_4000.context import AppContext
from weatherstar_4000.themes import CLASSIC_THEME


def test_extended_forecast_weekday_from_start_time():
    from weatherstar_4000.screens.extended_forecast import ExtendedForecastScreen

    screen = ExtendedForecastScreen.model_validate({})
    assert screen._weekday_abbrev({"startTime": "2026-09-05T18:00:00Z"}) == "SAT"
    assert screen._weekday_abbrev({"startTime": "2026-09-06T18:00:00-04:00"}) == "SUN"
    assert screen._weekday_abbrev({"startTime": "2026-09-07T18:00:00Z"}) == "MON"


def test_extended_forecast_weekday_from_name_when_no_start_time():
    from weatherstar_4000.screens.extended_forecast import ExtendedForecastScreen

    screen = ExtendedForecastScreen.model_validate({})
    assert screen._weekday_abbrev({"name": "Saturday"}) == "SAT"
    assert screen._weekday_abbrev({"name": "This Afternoon"}) != "THI"


def test_extended_forecast_day_label_prefers_daytime_period():
    from weatherstar_4000.screens.extended_forecast import ExtendedForecastScreen

    screen = ExtendedForecastScreen.model_validate({})
    day = {"name": "Sunday", "isDaytime": True, "startTime": "2026-09-06T18:00:00Z"}
    night = {"name": "Saturday Night", "isDaytime": False, "startTime": "2026-09-05T00:00:00Z"}
    assert screen._day_label(day, night) == "SUN"
    # If the pair opens at night (forecast begins overnight), label the next day.
    assert screen._day_label(night, day) == "SUN"


def test_extended_forecast_renders(fonts):
    from weatherstar_4000.screens.extended_forecast import ExtendedForecastScreen

    screen = ExtendedForecastScreen.model_validate({})
    surface = pygame.Surface((640, 480))
    ctx = AppContext(theme=CLASSIC_THEME, fonts=fonts)
    # Without data the screen draws its "NO DATA" message without raising.
    screen.draw(surface, ctx, 1 / 30)
