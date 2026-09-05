"""Tests for the Local Forecast screen's block-panel detection."""

from datetime import date, timedelta

import pygame

from weatherstar_4000.context import AppContext
from weatherstar_4000.themes import CLASSIC_THEME


def test_local_forecast_default_panels_when_no_background():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    screen = LocalForecastScreen.model_validate({})
    ctx = AppContext(theme=CLASSIC_THEME)
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


def _day(name, iso):
    return {"name": name, "isDaytime": True, "startTime": iso}


def _night(name, iso):
    return {"name": name, "isDaytime": False, "startTime": iso}


def test_outlook_uses_daytime_periods_when_available():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    periods = [
        _day("Today", "2026-09-05T18:00:00Z"),  # Sat
        _night("Tonight", "2026-09-05T23:00:00Z"),
        _day("Sunday", "2026-09-06T18:00:00Z"),  # Sun
        _night("Sunday Night", "2026-09-06T23:00:00Z"),
        _day("Monday", "2026-09-07T18:00:00Z"),  # Mon
        _day("Tuesday", "2026-09-08T18:00:00Z"),  # Tue
    ]
    columns = LocalForecastScreen._outlook_columns(periods)
    assert [c["name"] for c in columns] == ["Today", "Sunday", "Monday"]


def test_outlook_falls_back_to_raw_periods_without_day_flags():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    periods = [{"name": "Today"}, {"name": "Tonight"}, {"name": "Sunday"}]
    columns = LocalForecastScreen._outlook_columns(periods)
    assert [c["name"] for c in columns] == ["Today", "Tonight", "Sunday"]


def test_column_labels_today_tomorrow_weekday():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    today = date.today()
    screen_obj = LocalForecastScreen.model_validate({})
    columns = [
        _day("Today", f"{today}T18:00:00Z"),
        _day("Tomorrow", f"{today + timedelta(days=1)}T18:00:00Z"),
        _day("DayAfter", f"{today + timedelta(days=2)}T18:00:00Z"),
    ]
    labels = screen_obj._column_labels(columns)
    assert labels[0] == "TODAY"
    assert labels[1] == "TOMORROW"
    assert labels[2] == (today + timedelta(days=2)).strftime("%A").upper()


def test_column_labels_weekdays_when_outlook_not_today():
    from weatherstar_4000.screens.local_forecast import LocalForecastScreen

    base = date.today() + timedelta(days=1)
    screen_obj = LocalForecastScreen.model_validate({})
    columns = [_day("A", f"{base + timedelta(days=i)}T18:00:00Z") for i in range(3)]
    labels = screen_obj._column_labels(columns)
    for index, label in enumerate(labels):
        assert label == (base + timedelta(days=index)).strftime("%A").upper()
