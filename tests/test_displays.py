"""Tests for the main displays module (smoke coverage + pure helpers)."""

import time
from unittest.mock import MagicMock, patch

import pygame
import pytest

from weatherstar_4000.displays import WeatherStarDisplays

# draw_* methods exercised in the no-data smoke tests.
DRAW_METHODS_NO_DATA = [
    "draw_msn_news",
    "draw_reddit_news",
    "draw_current_conditions",
    "draw_local_forecast",
    "draw_extended_forecast",
    "draw_hourly_forecast",
    "draw_latest_observations",
    "draw_travel_cities",
    "draw_radar",
    "draw_almanac",
    "draw_hazards",
    "draw_marine_forecast",
    "draw_air_quality",
    "draw_temperature_graph",
    "draw_weather_records",
    "draw_sun_moon",
    "draw_wind_pressure",
    "draw_weekend_forecast",
    "draw_monthly_outlook",
    "draw_temperature_history",
    "draw_precipitation_history",
    "draw_uv_index",
    "draw_recent_earthquakes",
]

# Methods needing special setup are tested individually.
SPECIAL_METHODS = {
    "draw_header",
    "draw_background",
    "draw_local_news",
    "draw_scrolling_text",
    "draw_stock_market",
}


@pytest.fixture()
def display(ws_factory):
    return WeatherStarDisplays(ws_factory())


@pytest.mark.parametrize("method", DRAW_METHODS_NO_DATA)
def test_draw_methods_run_with_no_data(ws_factory, method):
    # Arrange
    instance = WeatherStarDisplays(ws_factory())

    # Act
    getattr(instance, method)()


def test_all_draw_methods_accounted_for():
    # Act
    methods = {
        name
        for name in dir(WeatherStarDisplays)
        if name.startswith("draw_") and callable(getattr(WeatherStarDisplays, name))
    }

    # Assert
    assert methods == set(DRAW_METHODS_NO_DATA) | SPECIAL_METHODS


# --- pure helpers ----------------------------------------------------------


@pytest.mark.parametrize(
    "degrees, expected",
    [(None, ""), (0, "N"), (90, "E"), (180, "S"), (270, "W"), (359, "N")],
)
def test_get_wind_direction(display, degrees, expected):
    # Assert
    assert display._get_wind_direction(degrees) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        (None, None),
        ("nourl", None),
        ("https://x/icons/land/day/skc?size=medium", "Clear"),
        ("https://x/icons/land/day/rain_showers", "Shower"),
        ("https://x/icons/land/day/tsra", "Thunderstorm"),
        ("https://x/icons/land/day/mystery", "Clear"),
    ],
)
def test_get_icon_name(display, url, expected):
    # Assert
    assert display._get_icon_name(url) == expected


# --- stock data fetching ---------------------------------------------------


def test_fetch_stock_data_returns_cached(display, monkeypatch):
    # Arrange
    display._stock_cache = {"time": 0, "data": [("DOW JONES", "1", "2", "green")]}
    monkeypatch.setattr("time.time", lambda: 100.0)

    with patch("requests.get") as mock_get:
        # Act
        result = display._fetch_stock_data()

        # Assert
        assert result == display._stock_cache["data"]
        mock_get.assert_not_called()


def test_fetch_stock_data_success_and_fallback(display, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 100.0)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    def fake_get(url, params=None, timeout=0):
        symbol = params["symbol"]
        if symbol == "DIA":
            return MagicMock(
                status_code=200,
                json=lambda: {"Global Quote": {"05. price": "30000.50", "09. change": "100.25"}},
            )
        if symbol == "SPY":
            return MagicMock(
                status_code=200,
                json=lambda: {"Global Quote": {"05. price": "5000", "09. change": "-20"}},
            )
        return MagicMock(status_code=500)

    with patch("requests.get", side_effect=fake_get):
        # Act
        result = display._fetch_stock_data()

    # Assert
    assert result[0] == ("DOW JONES", "30,000.50", "+100.25", "green")
    assert result[1][2] == "-20.00"
    assert result[1][3] == "red"
    assert result[2] == ("NASDAQ", "N/A", "N/A", "green")


def test_fetch_stock_data_handles_empty_quote(display, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 100.0)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    def fake_get(url, params=None, timeout=0):
        return MagicMock(status_code=200, json=lambda: {"Global Quote": {}})

    with patch("requests.get", side_effect=fake_get):
        # Act
        result = display._fetch_stock_data()

    # Assert
    assert all(item[1] == "N/A" for item in result)


def test_fetch_stock_data_handles_exception(display, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 100.0)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    with patch("requests.get", side_effect=Exception("down")):
        # Act
        result = display._fetch_stock_data()

    # Assert
    assert len(result) == 3
    assert result[0][1] == "N/A"


# --- draw_header / draw_background / local news / scrolling text -----------


def test_draw_header_single_line(display):
    # Act
    display.draw_header("Title")


def test_draw_header_dual_line_with_noaa(display):
    # Arrange
    display.ws.logos = {"noaa": pygame.Surface((10, 10))}

    # Act
    display.draw_header("Top", "Bottom", has_noaa=True)


def test_draw_background_present(display):
    # Arrange
    surface = pygame.Surface((640, 480))
    display.ws.backgrounds = {"1": surface}

    # Act
    display.draw_background("1")


def test_draw_background_missing_falls_back(display):
    # Arrange
    display.ws.backgrounds = {"2": pygame.Surface((640, 480))}

    # Act
    display.draw_background("3")


def test_draw_background_empty(display):
    # Arrange
    display.ws.backgrounds = {}

    # Act
    display.draw_background("1")


def test_draw_local_news(display):
    # Arrange
    display.ws.get_cached_city_name = lambda: "Testville"

    # Act
    display.draw_local_news()


def test_draw_scrolling_text_with_scroller(display):
    # Arrange
    display.ws.scroller = MagicMock()

    # Act
    display.draw_scrolling_text()


def test_draw_scrolling_text_fallback_without_scroller(display):
    # Arrange
    display.ws.scroller = None

    # Act
    display.draw_scrolling_text()


def test_draw_scrolling_text_swallows_errors(display, monkeypatch):
    # Arrange
    display.ws.scroller = MagicMock()
    display.ws.scroller.update.side_effect = RuntimeError("boom")
    display.ws.font_scroller = None

    # Act
    display.draw_scrolling_text()  # should not raise


def test_draw_stock_market(display):
    # Arrange
    display._fetch_stock_data = lambda: [
        ("DOW JONES", "30,000.50", "+100.25", "green"),
        ("S&P 500", "5,000.00", "-20.00", "red"),
    ]

    # Act
    display.draw_stock_market()
