"""Tests for the data fetchers module helpers."""

from unittest.mock import MagicMock

import pytest

from weatherstar_4000.data_fetchers import WeatherStarDataFetchers


@pytest.fixture()
def fetchers(ws_factory):
    return WeatherStarDataFetchers(ws_factory())


# --- get_cached_city_name --------------------------------------------------


def test_get_cached_city_name_uses_cache(fetchers, monkeypatch):
    # Arrange
    fetchers.ws.cached_city_name = "New York, NY"
    fetchers.ws.city_name_cached_at = 1_000_000
    monkeypatch.setattr("time.time", lambda: 1_000_100)

    import weatherstar_4000.get_local_news as gln

    monkeypatch.setattr(
        gln,
        "get_city_name_from_coords",
        lambda *a: (_ for _ in ()).throw(AssertionError),
    )

    # Act
    city = fetchers.get_cached_city_name()

    # Assert
    assert city == "New York, NY"


def test_get_cached_city_name_fetches_when_missing(fetchers, monkeypatch):
    # Arrange
    fetchers.ws.cached_city_name = None
    monkeypatch.setattr("time.time", lambda: 1_000_000)

    import weatherstar_4000.get_local_news as gln

    monkeypatch.setattr(gln, "get_city_name_from_coords", lambda lat, lon: "Chicago, IL")

    # Act
    city = fetchers.get_cached_city_name()

    # Assert
    assert city == "Chicago, IL"
    assert fetchers.ws.city_name_cached_at == 1_000_000


# --- radar helpers ---------------------------------------------------------


@pytest.mark.parametrize(
    "lat, lon, expected",
    [
        (45.0, -120.0, "PACNORTHWEST"),
        (37.0, -122.0, "PACSOUTHWEST"),
        (30.0, -110.0, "SOUTHROCKIES"),
        (45.0, -95.0, "NORTHROCKIES"),
        (37.0, -90.0, "SOUTHPLAINS"),
        (30.0, -90.0, "SOUTHMISSVLY"),
        (42.0, -80.0, "NORTHEAST"),
        (38.0, -78.0, "CENTGRTLAKES"),
        (33.0, -80.0, "SOUTHEAST"),
        (25.0, -80.0, "SOUTHEAST"),
    ],
)
def test_get_regional_radar_id(fetchers, lat, lon, expected):
    # Assert
    assert fetchers._get_regional_radar_id(lat, lon) == expected


def test_calculate_crop_area_centered():
    # Arrange
    fetchers = WeatherStarDataFetchers.__new__(WeatherStarDataFetchers)

    # Act
    left, top, right, bottom = fetchers._calculate_crop_area(37.0, -95.0, (500, 300))

    # Assert
    assert 0 <= left < right <= 500
    assert 0 <= top < bottom <= 300


def test_calculate_crop_area_clamps_left_top():
    # Arrange
    fetchers = WeatherStarDataFetchers.__new__(WeatherStarDataFetchers)

    # Act
    # Far west/north edge (lon=-125 -> x_norm 0, lat=50 -> y_norm 0).
    left, top, right, bottom = fetchers._calculate_crop_area(50.0, -125.0, (500, 300))

    # Assert
    assert left == 0
    assert top == 0


def test_calculate_crop_area_clamps_right_bottom():
    # Arrange
    fetchers = WeatherStarDataFetchers.__new__(WeatherStarDataFetchers)

    # Act
    # Far east/south edge (lon=-65 -> x_norm 1, lat=24 -> y_norm 1).
    left, top, right, bottom = fetchers._calculate_crop_area(24.0, -65.0, (500, 300))

    # Assert
    assert right == 500
    assert bottom == 300


# --- update_scroll_text ----------------------------------------------------


def _scroller():
    scroller = MagicMock()
    scroller.current_text = ""
    return scroller


def test_update_scroll_text_with_current(fetchers):
    # Arrange
    fetchers.ws.scroller = _scroller()
    fetchers.ws.weather_data = {
        "current": {
            "temperature": {"value": 20},
            "textDescription": "Partly Cloudy",
            "relativeHumidity": {"value": 55},
        },
        "forecast": {"periods": [{"name": "Today", "shortForecast": "Sunny"}]},
    }
    fetchers.ws.location = {"city": "Testville", "state": "TS"}

    # Act
    fetchers.update_scroll_text()

    # Assert
    assert "Testville" in fetchers.ws.scroller.current_text
    assert "68" in fetchers.ws.scroller.current_text  # 20C -> 68F
    assert "Partly Cloudy" in fetchers.ws.scroller.current_text


def test_update_scroll_text_without_current(fetchers):
    # Arrange
    fetchers.ws.scroller = _scroller()
    fetchers.ws.weather_data = {}
    fetchers.ws.location = {"city": "Testville", "state": "TS"}

    # Act
    fetchers.update_scroll_text()

    # Assert
    assert "WeatherStar 4000+ - Testville, TS" == fetchers.ws.scroller.current_text


def test_update_scroll_text_handles_error(fetchers):
    # Arrange
    fetchers.ws.scroller = MagicMock()

    class Boom:
        pass

    boom = Boom()
    boom.get = None  # not a dict

    fetchers.ws.weather_data = {"current": boom}
    fetchers.ws.location = {"city": "Testville", "state": "TS"}

    # Act
    fetchers.update_scroll_text()

    # Assert
    assert fetchers.ws.scroller.current_text == "WeatherStar 4000+ - Testville"
