"""Tests for the optimized weather API module (NOAA + Open Meteo + unified)."""

from unittest.mock import Mock

import pytest
import requests

from weatherstar_4000.weather_api import (
    NOAAWeatherAPI,
    OpenMeteoAPI,
    UnifiedWeatherAPI,
    WeatherAPIBase,
)


def _resp(json_data=None, status=200):
    resp = Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    resp.status_code = status
    return resp


# --- WeatherAPIBase --------------------------------------------------------


@pytest.fixture()
def base_api():
    return WeatherAPIBase(cache_ttl=300)


def test_cache_key_is_deterministic_for_same_args(base_api):
    # Assert
    assert base_api._cache_key("a", 1, "b") == base_api._cache_key("a", 1, "b")
    assert base_api._cache_key(1, "x") == '[1, "x"]'


def test_is_cache_valid_missing_key(base_api):
    # Assert
    assert base_api._is_cache_valid("k") is False


def test_is_cache_valid_uses_default_ttl(base_api):
    # Arrange
    base_api._set_cache("k", "v")

    # Assert
    assert base_api._is_cache_valid("k") is True

    # Arrange
    base_api.cache_time["k"] = 0

    # Assert
    assert base_api._is_cache_valid("k") is False


def test_is_cache_valid_honours_max_age(base_api, monkeypatch):
    # Arrange
    import time

    monkeypatch.setattr(time, "time", lambda: 1_000_000)
    base_api._set_cache("k", "v")
    base_api.cache_time["k"] = 1_000_000 - 50  # 50 seconds old

    # Assert
    assert base_api._is_cache_valid("k", max_age=100) is True
    assert base_api._is_cache_valid("k", max_age=10) is False


def test_get_cached_returns_none_when_missing(base_api):
    # Assert
    assert base_api._get_cached("nope") is None


def test_get_cached_returns_value_when_valid(base_api):
    # Arrange
    base_api._set_cache("k", {"a": 1})

    # Assert
    assert base_api._get_cached("k") == {"a": 1}


def test_get_cached_returns_none_when_expired(base_api):
    # Arrange
    base_api._set_cache("k", "v")
    base_api.cache_time["k"] = 0

    # Assert
    assert base_api._get_cached("k") is None


def test_set_cache_stores(base_api):
    # Act
    base_api._set_cache("k", "v")

    # Assert
    assert base_api.cache["k"] == "v"


def test_fetch_json_success(base_api):
    # Arrange
    base_api.session = Mock()
    base_api.session.get.return_value = _resp({"ok": True})

    # Act
    result = base_api._fetch_json("http://x", params={})

    # Assert
    assert result == {"ok": True}
    base_api.session.get.assert_called_once()


def test_fetch_json_returns_none_on_request_error(base_api):
    # Arrange
    base_api.session = Mock()
    base_api.session.get.side_effect = requests.RequestException("down")

    # Act
    result = base_api._fetch_json("http://x")

    # Assert
    assert result is None


def test_fetch_json_returns_none_on_decode_error(base_api):
    # Arrange
    import json

    resp = Mock()
    resp.raise_for_status.return_value = None
    resp.json.side_effect = json.JSONDecodeError("bad json", "doc", 0)
    base_api.session = Mock()
    base_api.session.get.return_value = resp

    # Act
    result = base_api._fetch_json("http://x")

    # Assert
    assert result is None


# --- NOAAWeatherAPI --------------------------------------------------------


@pytest.fixture()
def noaa():
    return NOAAWeatherAPI()


def test_noaa_grid_point_returns_cached(noaa):
    # Arrange
    noaa._set_cache(noaa._cache_key("grid", 40.0, -74.0), {"cached": True})

    # Act
    result = noaa.get_grid_point(40.0, -74.0)

    # Assert
    assert result["cached"] is True


def test_noaa_grid_point_success(noaa):
    # Arrange
    noaa._fetch_json = Mock(return_value={"properties": {"forecast": "http://f"}})

    # Act
    result = noaa.get_grid_point(40.7128, -74.0060)

    # Assert
    assert result == {"forecast": "http://f"}


def test_noaa_grid_point_returns_none_when_no_properties(noaa):
    # Arrange
    noaa._fetch_json = Mock(return_value={"nope": True})

    # Act
    result = noaa.get_grid_point(40.7128, -74.0060)

    # Assert
    assert result is None


def test_noaa_grid_point_returns_none_on_missing_data(noaa):
    # Arrange
    noaa._fetch_json = Mock(return_value=None)

    # Act
    result = noaa.get_grid_point(40.7128, -74.0060)

    # Assert
    assert result is None


def test_noaa_get_forecast_requires_grid(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value=None)

    # Act
    result = noaa.get_forecast(40.0, -74.0)

    # Assert
    assert result is None


def test_noaa_get_forecast_returns_cached(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={"forecast": "http://f"})
    noaa._set_cache(noaa._cache_key("forecast", 40.0, -74.0), {"cached": True})

    # Act
    result = noaa.get_forecast(40.0, -74.0)

    # Assert
    assert result["cached"] is True


def test_noaa_get_forecast_missing_url(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={})

    # Act
    result = noaa.get_forecast(40.0, -74.0)

    # Assert
    assert result is None


def test_noaa_get_forecast_success(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={"forecast": "http://f"})
    noaa._fetch_json = Mock(return_value={"properties": {"periods": []}})

    # Act
    result = noaa.get_forecast(40.0, -74.0)

    # Assert
    assert result == {"periods": []}


def test_noaa_get_forecast_no_properties(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={"forecast": "http://f"})
    noaa._fetch_json = Mock(return_value={"no": True})

    # Act
    result = noaa.get_forecast(40.0, -74.0)

    # Assert
    assert result is None


def test_noaa_get_current_requires_grid(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value=None)

    # Act
    result = noaa.get_current_conditions(40.0, -74.0)

    # Assert
    assert result is None


def test_noaa_get_current_missing_station_url(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={})

    # Act
    result = noaa.get_current_conditions(40.0, -74.0)

    # Assert
    assert result is None


def test_noaa_get_current_returns_cached(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={"observationStations": "http://s"})
    noaa._set_cache(noaa._cache_key("current", 40.0, -74.0), {"cached": True})

    # Act
    result = noaa.get_current_conditions(40.0, -74.0)

    # Assert
    assert result["cached"] is True


def test_noaa_get_current_no_stations(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={"observationStations": "http://s"})
    noaa._fetch_json = Mock(return_value={"features": []})

    # Act
    result = noaa.get_current_conditions(40.0, -74.0)

    # Assert
    assert result is None


def test_noaa_get_current_success_first_station(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={"observationStations": "http://s"})
    noaa._fetch_json = Mock(
        side_effect=[
            {"features": [{"properties": {"stationIdentifier": "KNYC"}}]},
            {"properties": {"temperature": 20}},
        ]
    )

    # Act
    result = noaa.get_current_conditions(40.0, -74.0)

    # Assert
    assert result == {"temperature": 20}


def test_noaa_get_current_skips_broken_stations(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={"observationStations": "http://s"})
    noaa._fetch_json = Mock(
        side_effect=[
            {
                "features": [
                    {"properties": {"stationIdentifier": "KNYC"}},
                    {"properties": {"stationIdentifier": "KJFK"}},
                ]
            },
            {"no-properties": True},  # first station fails
            {"properties": {"temperature": 30}},  # second station works
        ]
    )

    # Act
    result = noaa.get_current_conditions(40.0, -74.0)

    # Assert
    assert result == {"temperature": 30}


def test_noaa_get_current_station_without_identifier(noaa):
    # Arrange
    noaa.get_grid_point = Mock(return_value={"observationStations": "http://s"})
    noaa._fetch_json = Mock(
        side_effect=[
            {"features": [{"properties": {}}, {"properties": {"stationIdentifier": "KJFK"}}]},
            {"properties": {"temperature": 30}},
        ]
    )

    # Act
    result = noaa.get_current_conditions(40.0, -74.0)

    # Assert
    assert result == {"temperature": 30}


# --- OpenMeteoAPI (weather_api variant) ------------------------------------


@pytest.fixture()
def om():
    return OpenMeteoAPI()


def test_om_get_current_weather_returns_cached(om):
    # Arrange
    om._set_cache(om._cache_key("current", 40.0, -74.0, "imperial"), {"cached": True})

    # Act
    result = om.get_current_weather(40.0, -74.0)

    # Assert
    assert result["cached"] is True


def test_om_get_current_weather_success(om):
    # Arrange
    om._fetch_json = Mock(
        return_value={
            "current": {
                "temperature_2m": 20.0,
                "apparent_temperature": 19.0,
                "relative_humidity_2m": 60,
                "pressure_msl": 1013.0,
                "wind_speed_10m": 10.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 63,
            }
        }
    )

    # Act
    result = om.get_current_weather(40.0, -74.0)

    # Assert
    assert result["temperature"] == 20.0
    assert result["conditions"] == "Rain"


def test_om_get_current_weather_missing_current(om):
    # Arrange
    om._fetch_json = Mock(return_value={"no": True})

    # Act
    result = om.get_current_weather(40.0, -74.0)

    # Assert
    assert result is None


def test_om_get_forecast_returns_cached(om):
    # Arrange
    om._set_cache(om._cache_key("forecast", 40.0, -74.0, 7, "imperial"), {"cached": True})

    # Act
    result = om.get_forecast(40.0, -74.0)

    # Assert
    assert result["cached"] is True


def test_om_get_forecast_success(om):
    # Arrange
    om._fetch_json = Mock(
        return_value={
            "daily": {
                "time": ["2026-09-05", "2026-09-06"],
                "weather_code": [0, 63],
                "temperature_2m_max": [30.0, 25.0],
                "temperature_2m_min": [20.0, 15.0],
                "precipitation_sum": [0.0, 5.0],
                "wind_speed_10m_max": [5.0, 20.0],
            },
            "hourly": {
                "time": [f"2026-09-05T{i:02d}:00" for i in range(60)],
                "temperature_2m": list(range(60)),
                "precipitation": list(range(60)),
                "weather_code": list(range(60)),
            },
        }
    )

    # Act
    result = om.get_forecast(40.0, -74.0)

    # Assert
    assert len(result["daily"]) == 2
    assert result["daily"][1]["conditions"] == "Rain"
    assert len(result["hourly"]) == 48


def test_om_get_forecast_missing_data(om):
    # Arrange
    om._fetch_json = Mock(return_value=None)

    # Act
    result = om.get_forecast(40.0, -74.0)

    # Assert
    assert result is None


def test_process_current_data_maps_fields(om):
    # Act
    result = om._process_current_data(
        {
            "current": {
                "temperature_2m": 20.0,
                "apparent_temperature": 19.0,
                "relative_humidity_2m": 60,
                "pressure_msl": 1013.0,
                "wind_speed_10m": 10.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 63,
            }
        }
    )

    # Assert
    assert result["humidity"] == 60
    assert result["conditions"] == "Rain"


@pytest.mark.parametrize(
    "code, expected",
    [
        (0, "Clear"),
        (1, "Mostly Clear"),
        (2, "Partly Cloudy"),
        (3, "Cloudy"),
        (45, "Fog"),
        (48, "Freezing Fog"),
        (51, "Light Drizzle"),
        (53, "Drizzle"),
        (61, "Light Rain"),
        (63, "Rain"),
        (65, "Heavy Rain"),
        (71, "Light Snow"),
        (73, "Snow"),
        (75, "Heavy Snow"),
        (95, "Thunderstorm"),
        (200, "Unknown"),
    ],
)
def test_om_weather_condition_mapping(om, code, expected):
    # Assert
    assert om._get_weather_condition(code) == expected


# --- UnifiedWeatherAPI -----------------------------------------------------


@pytest.fixture()
def unified():
    return UnifiedWeatherAPI()


@pytest.mark.parametrize(
    "lat, lon, expected",
    [
        # Continental US interior + exact boundaries
        (40.0, -100.0, True),
        (24.0, -125.0, True),
        (49.0, -66.0, True),
        (23.9, -100.0, False),
        (49.1, -100.0, False),
        (40.0, -125.1, False),
        (40.0, -65.9, False),
        # Alaska
        (51.0, -180.0, True),
        (72.0, -129.0, True),
        (50.0, -150.0, False),
        # Hawaii
        (18.0, -161.0, True),
        (23.0, -154.0, True),
        (17.0, -157.0, False),
        # International
        (51.5, -0.1, False),
        (35.0, 139.0, False),
    ],
)
def test_is_us_location(unified, lat, lon, expected):
    # Assert
    assert unified._is_us_location(lat, lon) is expected


def test_get_weather_prefers_noaa_for_us(unified):
    # Arrange
    unified.noaa.get_current_conditions = Mock(return_value={"temp": 20})
    unified.noaa.get_forecast = Mock(return_value={"periods": []})
    unified.open_meteo.get_current_weather = Mock(return_value={"temp": 30})
    unified.open_meteo.get_forecast = Mock(return_value={})

    # Act
    result = unified.get_weather(40.0, -74.0)

    # Assert
    assert result["source"] == "NOAA"
    unified.open_meteo.get_current_weather.assert_not_called()


def test_get_weather_falls_back_to_open_meteo_when_noaa_empty(unified):
    # Arrange
    unified.noaa.get_current_conditions = Mock(return_value=None)
    unified.noaa.get_forecast = Mock(return_value=None)
    unified.open_meteo.get_current_weather = Mock(return_value={"temp": 30})
    unified.open_meteo.get_forecast = Mock(return_value={})

    # Act
    result = unified.get_weather(40.0, -74.0)

    # Assert
    assert result["source"] == "Open Meteo"


def test_get_weather_open_meteo_for_international(unified):
    # Arrange
    unified.open_meteo.get_current_weather = Mock(return_value={"temp": 30})
    unified.open_meteo.get_forecast = Mock(return_value={})
    unified.noaa.get_current_conditions = Mock(return_value={"temp": 1})

    # Act
    result = unified.get_weather(51.5, -0.1)

    # Assert
    assert result["source"] == "Open Meteo"


def test_get_weather_prefer_international_skips_noaa(unified):
    # Arrange
    unified.open_meteo.get_current_weather = Mock(return_value={"temp": 30})
    unified.open_meteo.get_forecast = Mock(return_value={})
    unified.noaa.get_current_conditions = Mock(return_value={"temp": 1})

    # Act
    result = unified.get_weather(40.0, -74.0, prefer_international=True)

    # Assert
    assert result["source"] == "Open Meteo"
