"""Tests for the entrypoint module helpers (no full app construction)."""

from unittest.mock import MagicMock, patch

import pytest

import weatherstar_4000.weatherstar_logger as wl


@pytest.fixture(scope="module")
def main_module():
    """Import weatherstar_4000.__main__ while stubbing init_logger.

    The module calls ``init_logger()`` at import time, which constructs a
    WeatherStarLogger that probes pygame and quits it. We swap init_logger for
    a no-op stub so importing the module has no side effects.
    """
    fake = MagicMock()
    fake.main_logger = MagicMock()
    fake.api_logger = MagicMock()
    fake.error_logger = MagicMock()

    original_init = wl.init_logger
    original_logger = wl.logger
    wl.init_logger = lambda *a, **k: fake
    try:
        import weatherstar_4000.__main__ as m
    finally:
        wl.init_logger = original_init
        wl.logger = original_logger
    return m


@pytest.fixture(scope="module")
def module_logger(main_module):
    return main_module.logger


# --- DisplayMode enum ------------------------------------------------------


def test_display_mode_has_expected_members(main_module):
    # Assert
    expected = {
        "CURRENT_CONDITIONS": "current-weather",
        "LOCAL_FORECAST": "local-forecast",
        "EXTENDED_FORECAST": "extended-forecast",
        "RADAR": "radar",
        "SEVERE_WEATHER_ALERT": "severe-weather-alert",
    }
    for name, value in expected.items():
        assert main_module.DisplayMode[name].value == value


# --- WeatherIcon -----------------------------------------------------------


@pytest.mark.parametrize(
    "code, is_night, expected",
    [
        ("skc", False, "Sunny.gif"),
        ("skc", True, "Clear.gif"),
        ("few", False, "Partly-Cloudy.gif"),
        ("few", True, "Mostly-Clear.gif"),
        ("sct", False, "Partly-Cloudy.gif"),
        ("bkn", False, "Cloudy.gif"),
        ("ovc", True, "Cloudy.gif"),
        ("fog", False, "Fog.gif"),
        ("smoke", False, "Smoke.gif"),
        ("rain", True, "Rain.gif"),
        ("rain_showers", False, "Shower.gif"),
        ("tsra", False, "Scattered-Thunderstorms-Day.gif"),
        ("tsra", True, "Scattered-Thunderstorms-Night.gif"),
        ("snow", False, "Snow.gif"),
        ("sleet", False, "Sleet.gif"),
        ("frzra", False, "Freezing-Rain.gif"),
        ("wind", False, "Windy.gif"),
        ("unknown", False, "No-Data.gif"),
    ],
)
def test_weather_icon_mapping(main_module, code, is_night, expected):
    # Assert
    assert main_module.WeatherIcon.get_icon(code, is_night) == expected


# --- ScrollingText ---------------------------------------------------------


def test_scrolling_text_init_and_add_item(main_module, fonts):
    # Act
    scroller = main_module.ScrollingText(fonts["font_normal"])

    # Assert
    assert scroller.current_text == ""

    # Act
    scroller.add_item("Hello")

    # Assert
    assert scroller.text_items == ["Hello"]


def test_scrolling_text_update_cycles_items(main_module, fonts, monkeypatch):
    # Arrange
    scroller = main_module.ScrollingText(fonts["font_normal"])
    scroller.add_item("Next")
    scroller.add_item("Second")
    scroller.scroll_x = -1000  # well off the left edge
    scroller.current_text = "abc"
    monkeypatch.setattr("time.time", lambda: 200.0)
    scroller.last_update = 100.0

    # Act
    scroller.update()

    # Assert
    assert scroller.scroll_x == main_module.SCREEN_WIDTH
    assert scroller.current_text == "Next"


def test_scrolling_text_update_no_cycle_when_visible(main_module, fonts, monkeypatch):
    # Arrange
    scroller = main_module.ScrollingText(fonts["font_normal"])
    scroller.current_text = "visible"
    scroller.scroll_x = 400
    monkeypatch.setattr("time.time", lambda: 100.5)
    scroller.last_update = 100.0

    # Act
    scroller.update()

    # Assert
    assert 0 < scroller.scroll_x < 400  # moved left but did not reset


def test_scrolling_text_draw_renders_current(main_module, screen, fonts, display):
    # Arrange
    scroller = main_module.ScrollingText(fonts["font_normal"])
    scroller.current_text = "Hello"

    # Act
    scroller.draw(screen, 400)


def test_scrolling_text_draw_empty_noop(main_module, screen, fonts):
    # Arrange
    scroller = main_module.ScrollingText(fonts["font_normal"])
    scroller.current_text = ""

    # Act
    scroller.draw(screen, 400)


# --- get_automatic_location ------------------------------------------------


def test_automatic_location_primary_service(main_module):
    # Arrange
    resp = MagicMock(status_code=200)
    resp.json.return_value = {
        "latitude": 40.7,
        "longitude": -74.0,
        "city": "New York",
        "region": "NY",
        "country_code": "US",
    }

    # Act
    with patch("requests.get", return_value=resp) as mock_get:
        result = main_module.get_automatic_location()

    # Assert
    assert result == (40.7, -74.0, "New York, NY")
    mock_get.assert_called_once()


def test_automatic_location_falls_to_second_service(main_module):
    # Arrange
    non_us = MagicMock(status_code=200)
    non_us.json.return_value = {
        "latitude": 48.8,
        "longitude": 2.3,
        "city": "Paris",
        "region": "",
        "country_code": "FR",
    }
    us_resp = MagicMock(status_code=200)
    us_resp.json.return_value = {
        "status": "success",
        "lat": 34.0,
        "lon": -118.2,
        "city": "Los Angeles",
        "regionName": "CA",
        "countryCode": "US",
    }

    # Act
    with patch("requests.get", side_effect=[non_us, us_resp]) as mock_get:
        result = main_module.get_automatic_location()

    # Assert
    assert result == (34.0, -118.2, "Los Angeles, CA")
    assert mock_get.call_count == 2


def test_automatic_location_returns_none_when_all_fail(main_module):
    # Arrange
    failing = MagicMock(status_code=500)

    # Act
    with patch("requests.get", return_value=failing) as mock_get:
        result = main_module.get_automatic_location()

    # Assert
    assert result is None
    assert mock_get.call_count == 2


def test_automatic_location_handles_exceptions(main_module):
    # Act
    with patch("requests.get", side_effect=Exception("network down")):
        result = main_module.get_automatic_location()

    # Assert
    assert result is None


# --- NOAAWeatherAPI (entrypoint variant) ----------------------------------


@pytest.fixture()
def noaa(main_module):
    return main_module.NOAAWeatherAPI()


def _response(data=None, status=200):
    resp = MagicMock(status_code=status)
    resp.json.return_value = data or {}
    return resp


def test_noaa_initialization(noaa):
    # Assert
    assert noaa.base_url == "https://api.weather.gov"
    assert noaa.cache == {}
    assert noaa.cache_time == {}


def test_noaa_cache_validity(noaa, monkeypatch):
    # Assert
    assert noaa._is_cache_valid("missing") is False

    # Arrange
    noaa._cache_data("k", {"a": 1})

    # Assert
    assert noaa._is_cache_valid("k") is True

    # Arrange
    noaa.cache_time["k"] = 0

    # Assert
    assert noaa._is_cache_valid("k") is False


def test_noaa_get_point_data_success_and_cache(noaa):
    # Arrange
    data = {"properties": {"forecast": "http://f"}}

    # Act
    with patch("requests.get", return_value=_response(data)):
        result = noaa.get_point_data(40.0, -74.0)

    # Assert
    assert result == data

    # Act
    # Second call served from cache without network.
    with patch("requests.get", side_effect=AssertionError):
        result = noaa.get_point_data(40.0, -74.0)

    # Assert
    assert result == data


def test_noaa_get_point_data_failure(noaa):
    # Act
    with patch("requests.get", return_value=_response(status=500)):
        result = noaa.get_point_data(40.0, -74.0)

    # Assert
    assert result is None


def test_noaa_get_point_data_exception(noaa):
    # Act
    with patch("requests.get", side_effect=Exception("down")):
        result = noaa.get_point_data(40.0, -74.0)

    # Assert
    assert result is None


def test_noaa_get_stations(noaa):
    # Arrange
    data = {"features": [{"id": 1}, {"id": 2}]}

    # Act
    with patch("requests.get", return_value=_response(data)):
        result = noaa.get_stations("http://stations")

    # Assert
    assert result == data

    # Act
    with patch("requests.get", side_effect=AssertionError):
        result = noaa.get_stations("http://stations")

    # Assert
    assert result == data


def test_noaa_get_current_observations(noaa):
    # Arrange
    data = {"properties": {"temperature": 20}}

    # Act
    with patch("requests.get", return_value=_response(data)):
        result = noaa.get_current_observations("KNYC")

    # Assert
    assert result == data

    # Act
    with patch("requests.get", side_effect=AssertionError):
        result = noaa.get_current_observations("KNYC")

    # Assert
    assert result == data


def test_noaa_get_forecast(noaa):
    # Arrange
    data = {"properties": {"periods": [{"x": 1}]}}

    # Act
    with patch("requests.get", return_value=_response(data)) as mock_get:
        result = noaa.get_forecast("OKX", 40, -74)

    # Assert
    assert result == data
    assert mock_get.call_args[1]["params"] == {"units": "us"}

    # Act
    with patch("requests.get", side_effect=AssertionError):
        result = noaa.get_forecast("OKX", 40, -74)

    # Assert
    assert result == data


def test_noaa_get_hourly_forecast(noaa):
    # Arrange
    data = {"properties": {"periods": []}}

    # Act
    with patch("requests.get", return_value=_response(data)):
        result = noaa.get_hourly_forecast("OKX", 40, -74, units="si")

    # Assert
    assert result == data

    # Act
    with patch("requests.get", side_effect=AssertionError):
        result = noaa.get_hourly_forecast("OKX", 40, -74, units="si")

    # Assert
    assert result == data


# --- WeatherStar4000Complete logic methods ---------------------------------


def _build_state(main_module):
    ws = main_module.WeatherStar4000Complete.__new__(main_module.WeatherStar4000Complete)
    ws.settings = {}
    ws.display_list = []
    ws.displays = []
    ws.current_display_index = 0
    ws.display_timer = 0
    ws.narrator = MagicMock()
    ws.weather_data = {}
    return ws


def test_update_display_list_defaults(main_module):
    # Arrange
    ws = _build_state(main_module)
    ws.settings = {
        "show_marine": False,
        "show_msn": False,
        "show_reddit": False,
        "show_local_news": False,
    }

    # Act
    ws.update_display_list()

    # Assert
    assert len(ws.displays) == 12
    assert main_module.DisplayMode.PROGRESS not in ws.displays


def test_update_display_list_with_optional(main_module):
    # Arrange
    ws = _build_state(main_module)
    ws.settings = {
        "show_marine": True,
        "show_msn": True,
        "show_reddit": True,
        "show_local_news": True,
    }

    # Act
    ws.update_display_list()

    # Assert
    for mode in [
        main_module.DisplayMode.MARINE_FORECAST,
        main_module.DisplayMode.MSN_NEWS,
        main_module.DisplayMode.REDDIT_NEWS,
        main_module.DisplayMode.LOCAL_NEWS,
    ]:
        assert mode in ws.displays


def test_cycle_display_advances(main_module):
    # Arrange
    ws = _build_state(main_module)
    ws.displays = [
        main_module.DisplayMode.CURRENT_CONDITIONS,
        main_module.DisplayMode.RADAR,
        main_module.DisplayMode.HAZARDS,
    ]
    ws.current_display_index = 0

    # Act
    ws.cycle_display()

    # Assert
    assert ws.current_display_index == 1
    assert ws.display_timer == 0


def test_cycle_display_wraps(main_module):
    # Arrange
    ws = _build_state(main_module)
    ws.displays = [
        main_module.DisplayMode.CURRENT_CONDITIONS,
        main_module.DisplayMode.RADAR,
    ]
    ws.current_display_index = 1

    # Act
    ws.cycle_display()

    # Assert
    assert ws.current_display_index == 0


def test_cycle_display_announces_when_enabled(main_module):
    # Arrange
    ws = _build_state(main_module)
    ws.settings = {"voice_narration": True}
    ws.displays = [main_module.DisplayMode.CURRENT_CONDITIONS, main_module.DisplayMode.RADAR]
    ws.current_display_index = 0

    # Act
    ws.cycle_display()

    # Assert
    ws.narrator.set_enabled.assert_called_once_with(True)
    ws.narrator.announce_display.assert_called_once()


# --- wind direction helper -------------------------------------------------


@pytest.mark.parametrize(
    "degrees, expected",
    [(None, ""), (0, "N"), (45, "NE"), (90, "E"), (359, "N")],
)
def test_ws_get_wind_direction(main_module, degrees, expected):
    # Arrange
    ws = main_module.WeatherStar4000Complete.__new__(main_module.WeatherStar4000Complete)

    # Act
    result = ws._get_wind_direction(degrees)

    # Assert
    assert result == expected
