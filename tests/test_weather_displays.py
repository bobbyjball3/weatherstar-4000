"""Tests for the specialized weather display module (smoke + pure helpers)."""

import datetime as _dt

import pytest

import weatherstar_4000.weather_displays as wd
from weatherstar_4000.weather_displays import WeatherStarSpecializedDisplays


@pytest.fixture()
def display(mock_ws):
    return WeatherStarSpecializedDisplays(mock_ws)


def _periods():
    return [
        {"name": "Today", "isDaytime": True, "temperature": 68},
        {"name": "Tonight", "isDaytime": False, "temperature": 45},
        {"name": "Tuesday", "isDaytime": True, "temperature": 72},
        {"name": "Tuesday Night", "isDaytime": False, "temperature": 48},
    ]


def _current(**overrides):
    base = {
        "temperature": {"value": 20},
        "relativeHumidity": {"value": 55},
        "dewpoint": {"value": 10},
        "barometricPressure": {"value": 101300},
        "visibility": {"value": 16000},
        "windSpeed": {"value": 16},
        "windDirection": {"value": 90},
        "windGust": {"value": 25},
        "windChill": {"value": 5},
        "heatIndex": {"value": None},
    }
    base.update(overrides)
    return base


# --- pure helpers ----------------------------------------------------------


@pytest.mark.parametrize(
    "degrees, expected",
    [
        (None, ""),
        (0, "N"),
        (30, "NNE"),
        (45, "NE"),
        (90, "E"),
        (135, "SE"),
        (180, "S"),
        (225, "SW"),
        (270, "W"),
        (315, "NW"),
        (359, "N"),
    ],
)
def test_get_wind_direction(display, degrees, expected):
    # Assert
    assert display._get_wind_direction(degrees) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        (None, None),
        ("no-slash", None),
        ("https://api.weather.gov/icons/land/day/skc?size=medium", "Clear"),
        ("https://api.weather.gov/icons/land/day/few", "Clear"),
        ("https://api.weather.gov/icons/land/day/sct", "Partly-Cloudy"),
        ("https://api.weather.gov/icons/land/day/bkn", "Cloudy"),
        ("https://api.weather.gov/icons/land/day/ovc", "Cloudy"),
        ("https://api.weather.gov/icons/land/day/rain", "Rain"),
        ("https://api.weather.gov/icons/land/day/rain_showers", "Shower"),
        ("https://api.weather.gov/icons/land/day/tsra", "Thunderstorm"),
        ("https://api.weather.gov/icons/land/day/snow", "Light-Snow"),
        ("https://api.weather.gov/icons/land/day/fog", "Fog"),
        ("https://api.weather.gov/icons/land/day/wind", "Windy"),
        ("https://api.weather.gov/icons/land/day/unknown_code", "Clear"),
    ],
)
def test_get_icon_name(display, url, expected):
    # Assert
    assert display._get_icon_name(url) == expected


# --- draw methods (smoke) --------------------------------------------------


def test_draw_almanac_with_data(display):
    # Arrange
    display.ws.weather_data = {"current": _current()}

    # Act
    display.draw_almanac()


def test_draw_almanac_empty_current(display):
    # Arrange
    display.ws.weather_data = {"current": {}}

    # Act
    display.draw_almanac()


def test_draw_temperature_graph_empty(display):
    # Arrange
    display.ws.weather_data = {"forecast": {"periods": []}}

    # Act
    display.draw_temperature_graph()


def test_draw_temperature_graph_with_periods(display):
    # Arrange
    display.ws.weather_data = {"forecast": {"periods": _periods()}}

    # Act
    display.draw_temperature_graph()


def test_draw_weather_records(display):
    # Act
    display.draw_weather_records()


@pytest.mark.parametrize(
    "day",
    [1, 10, 14, 18, 25],
)
def test_draw_sun_moon_phases(display, monkeypatch, day):
    # Arrange
    fixed = _dt.datetime(2026, 1, day, 12, 0, 0)
    monkeypatch.setattr(
        wd,
        "datetime",
        type("_FixedDT", (), {"now": staticmethod(lambda: fixed)}),
    )

    # Act
    display.draw_sun_moon()


def test_draw_wind_pressure_full(display):
    # Arrange
    display.ws.weather_data = {"current": _current()}

    # Act
    display.draw_wind_pressure()


def test_draw_wind_pressure_heat_index_branch(display):
    # Arrange
    current = _current()
    current.pop("windChill")  # API omits wind chill when there is a heat index
    current["heatIndex"] = {"value": 30}
    display.ws.weather_data = {"current": current}

    # Act
    display.draw_wind_pressure()


def test_draw_wind_pressure_minimal(display):
    # Arrange
    display.ws.weather_data = {"current": {}}

    # Act
    display.draw_wind_pressure()


def test_draw_monthly_outlook(display):
    # Act
    display.draw_monthly_outlook()
