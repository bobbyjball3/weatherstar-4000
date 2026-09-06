"""Tests for the Local Forecast screen's block-panel detection."""

import datetime
from datetime import date, timedelta

import pygame

from weatherstar_4000.context import AppContext
from weatherstar_4000.datasources.noaa import ForecastPeriod


def _period(name, is_daytime, when):
    return ForecastPeriod(name=name, is_daytime=is_daytime, start_time=when)


def _day(name, when):
    return _period(name, True, when)


def _night(name, when):
    return _period(name, False, when)


def _dt(d):
    return datetime.datetime.combine(d, datetime.time(18))


def test_local_forecast_default_panels_when_no_background():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    screen = LocalForecastScreen.model_validate({})
    ctx = AppContext()
    panels = screen._panels(ctx)
    assert len(panels) == 3
    x0, x1, top, bottom = panels[1]
    assert x0 < x1 and top < bottom


def test_local_forecast_detects_panels_in_background_art():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    image = pygame.Surface((640, 480))
    image.fill((200, 120, 40))  # warm sky, not panel-like
    blue = (30, 30, 220)
    for x0, x1 in ((40, 209), (234, 403), (428, 597)):
        pygame.draw.rect(image, blue, pygame.Rect(x0, 103, x1 - x0 + 1, 291))
    panels = LocalForecastScreen._detect_panels(image)
    assert len(panels) == 3
    assert panels[0][:2] == (40, 209)
    assert panels[1][:2] == (234, 403)
    assert panels[2][:2] == (428, 597)
    for _x0, _x1, top, bottom in panels:
        assert top == 103
        assert bottom == 393


def test_local_forecast_detection_returns_empty_for_art_without_panels():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    image = pygame.Surface((640, 480))
    image.fill((200, 120, 40))
    assert LocalForecastScreen._detect_panels(image) == ()
    assert LocalForecastScreen._detect_panels(None) == ()


def test_outlook_uses_daytime_periods_when_available():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    sat = date(2026, 9, 5)
    periods = [
        _day("Today", _dt(sat)),
        _night("Tonight", _dt(sat)),
        _day("Sunday", _dt(sat + timedelta(days=1))),
        _night("Sunday Night", _dt(sat + timedelta(days=1))),
        _day("Monday", _dt(sat + timedelta(days=2))),
        _day("Tuesday", _dt(sat + timedelta(days=3))),
    ]
    columns = LocalForecastScreen._outlook_columns(periods)
    assert [c.name for c in columns] == ["Today", "Sunday", "Monday"]


def test_outlook_falls_back_to_raw_periods_without_day_flags():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    periods = [
        ForecastPeriod(name="Today"),
        ForecastPeriod(name="Tonight"),
        ForecastPeriod(name="Sunday"),
    ]
    columns = LocalForecastScreen._outlook_columns(periods)
    assert [c.name for c in columns] == ["Today", "Tonight", "Sunday"]


def test_column_labels_today_tomorrow_weekday():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    today = date.today()
    screen_obj = LocalForecastScreen.model_validate({})
    columns = [
        _day("Today", _dt(today)),
        _day("Tomorrow", _dt(today + timedelta(days=1))),
        _day("DayAfter", _dt(today + timedelta(days=2))),
    ]
    labels = screen_obj._column_labels(columns)
    assert labels[0] == "TODAY"
    assert labels[1] == "TOMORROW"
    assert labels[2] == (today + timedelta(days=2)).strftime("%A").upper()


def test_column_labels_weekdays_when_outlook_not_today():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    base = date.today() + timedelta(days=1)
    screen_obj = LocalForecastScreen.model_validate({})
    columns = [_day("A", _dt(base + timedelta(days=i))) for i in range(3)]
    labels = screen_obj._column_labels(columns)
    for index, label in enumerate(labels):
        assert label == (base + timedelta(days=index)).strftime("%A").upper()
