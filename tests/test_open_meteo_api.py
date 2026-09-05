"""Tests for the standalone Open Meteo API client."""

from unittest.mock import patch

import pytest

from weatherstar_4000.open_meteo_api import OpenMeteoAPI

API = OpenMeteoAPI


@pytest.fixture()
def api():
    return API()


CURRENT_PAYLOAD = {
    "current": {
        "temperature_2m": 20.0,
        "apparent_temperature": 19.0,
        "relative_humidity_2m": 60,
        "pressure_msl": 1013.0,
        "wind_speed_10m": 10.0,
        "wind_direction_10m": 180,
        "wind_gusts_10m": 15.0,
        "precipitation": 0.0,
        "weather_code": 63,
    },
    "timezone": "America/New_York",
}

FORECAST_PAYLOAD = {
    "daily": {
        "time": ["2026-09-05", "2026-09-06"],
        "weather_code": [0, 63],
        "temperature_2m_max": [30.0, 25.0],
        "temperature_2m_min": [20.0, 15.0],
        "precipitation_sum": [0.0, 5.0],
        "rain_sum": [0.0, 5.0],
        "snowfall_sum": [0.0, 0.0],
        "precipitation_probability_max": [0, 80],
        "wind_speed_10m_max": [5.0, 20.0],
        "wind_gusts_10m_max": [10.0, 30.0],
        "sunrise": ["06:00", "06:01"],
        "sunset": ["18:00", "18:01"],
    },
    "hourly": {
        "time": ["2026-09-05T00:00", "2026-09-05T01:00", "2026-09-05T02:00"],
        "temperature_2m": [20.0, 21.0, 22.0],
        "relative_humidity_2m": [60, 61, 62],
        "precipitation": [0.0, 0.0, 0.0],
        "weather_code": [0, 1, 2],
        "wind_speed_10m": [5.0, 6.0, 7.0],
        "wind_direction_10m": [90, 90, 90],
    },
    "timezone": "America/New_York",
}


# --- cache primitives -------------------------------------------------------


def test_initialization(api):
    # Assert
    assert api.base_url == "https://api.open-meteo.com/v1"
    assert api.geocoding_url == "https://geocoding-api.open-meteo.com/v1"
    assert api.cache == {}
    assert api.cache_time == {}


def test_is_cache_valid_returns_false_for_unknown_key(api):
    # Assert
    assert api._is_cache_valid("nope", 300) is False


def test_is_cache_valid_accepts_fresh_entry(api):
    # Arrange
    api._cache_data("k", "v")

    # Assert
    assert api._is_cache_valid("k", 300) is True


def test_is_cache_valid_expires_entry(api):
    # Arrange
    api._cache_data("k", "v")
    api.cache_time["k"] = 0  # long ago

    # Assert
    assert api._is_cache_valid("k", 300) is False


def test_cache_data_stores_payload(api):
    # Act
    api._cache_data("k", {"a": 1})

    # Assert
    assert api.cache["k"] == {"a": 1}
    assert api.cache_time["k"] > 0


# --- get_location_name -----------------------------------------------------


def test_get_location_name_uses_cache(api):
    # Arrange
    api._cache_data("location_40.0_-74.0", "Cached City")

    # Act
    with patch("requests.get") as mock_get:
        result = api.get_location_name(40.0, -74.0)

    # Assert
    assert result == "Cached City"
    mock_get.assert_not_called()


def test_get_location_name_builds_city_state(api):
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [{"name": "New York", "country": "US", "admin1": "NY"}]
        }

        # Act
        result = api.get_location_name(40.7128, -74.0060)

    # Assert
    assert result == "New York, NY"


def test_get_location_name_uses_country_when_no_admin1(api):
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [{"name": "Paris", "country": "France", "admin1": ""}]
        }

        # Act
        result = api.get_location_name(48.8566, 2.3522)

    # Assert
    assert result == "Paris, France"


def test_get_location_name_falls_back_to_coords_without_city(api):
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": [{"name": "", "country": ""}]}

        # Act
        result = api.get_location_name(40.0, -74.0)

    # Assert
    assert result == "40.00, -74.00"


def test_get_location_name_falls_back_to_coords_on_exception(api):
    # Act
    with patch("requests.get", side_effect=Exception("timeout")):
        result = api.get_location_name(40.0, -74.0)

    # Assert
    assert result == "40.00, -74.00"


# --- get_current_weather ---------------------------------------------------


def test_get_current_weather_returns_cache(api):
    # Arrange
    api._cache_data("current_40.0_-74.0_imperial", {"cached": True})

    # Act
    with patch("requests.get") as mock_get:
        result = api.get_current_weather(40.0, -74.0)

    # Assert
    assert result == {"cached": True}
    mock_get.assert_not_called()


def test_get_current_weather_success(api, monkeypatch):
    # Arrange
    monkeypatch.setattr(api, "get_location_name", lambda lat, lon: "Test City")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = CURRENT_PAYLOAD

        # Act
        result = api.get_current_weather(40.0, -74.0)

    # Assert
    assert result["temperature"] == 20.0
    assert result["conditions"] == "Rain"
    assert result["location"] == "Test City"
    assert result["timezone"] == "America/New_York"


def test_get_current_weather_returns_empty_on_error(api, monkeypatch):
    # Arrange
    monkeypatch.setattr(api, "get_location_name", lambda lat, lon: "Test City")

    # Act
    with patch("requests.get", side_effect=Exception("boom")):
        result = api.get_current_weather(40.0, -74.0)

    # Assert
    assert result == {}


def test_get_current_weather_returns_empty_on_bad_status(api):
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500

        # Act
        result = api.get_current_weather(40.0, -74.0)

    # Assert
    assert result == {}


# --- get_forecast ----------------------------------------------------------


def test_get_forecast_returns_cache(api):
    # Arrange
    api._cache_data("forecast_40.0_-74.0_7_imperial", {"cached": True})

    # Act
    with patch("requests.get") as mock_get:
        result = api.get_forecast(40.0, -74.0)

    # Assert
    assert result == {"cached": True}
    mock_get.assert_not_called()


def test_get_forecast_success(api, monkeypatch):
    # Arrange
    monkeypatch.setattr(api, "get_location_name", lambda lat, lon: "Test City")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = FORECAST_PAYLOAD

        # Act
        result = api.get_forecast(40.0, -74.0)

    # Assert
    assert len(result["daily"]) == 2
    assert result["daily"][1]["conditions"] == "Rain"
    assert len(result["hourly"]) == 3
    assert result["hourly"][0]["temperature"] == 20.0
    assert result["location"] == "Test City"


def test_get_forecast_truncates_hourly_to_48(api, monkeypatch):
    # Arrange
    monkeypatch.setattr(api, "get_location_name", lambda lat, lon: "Test City")
    payload = dict(FORECAST_PAYLOAD)
    payload["hourly"] = {
        "time": [f"2026-09-05T{i:02d}:00" for i in range(60)],
        "temperature_2m": list(range(60)),
        "relative_humidity_2m": list(range(60)),
        "precipitation": list(range(60)),
        "weather_code": list(range(60)),
        "wind_speed_10m": list(range(60)),
        "wind_direction_10m": list(range(60)),
    }
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = payload

        # Act
        result = api.get_forecast(40.0, -74.0)

    # Assert
    assert len(result["hourly"]) == 48


def test_get_forecast_returns_empty_on_error(api):
    # Act
    with patch("requests.get", side_effect=Exception("boom")):
        result = api.get_forecast(40.0, -74.0)

    # Assert
    assert result == {}


def test_get_forecast_returns_empty_on_bad_status(api):
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500

        # Act
        result = api.get_forecast(40.0, -74.0)

    # Assert
    assert result == {}


# --- air quality -----------------------------------------------------------


AIR_QUALITY_PAYLOAD = {
    "current": {
        "us_aqi": 42,
        "pm10": 5.0,
        "pm2_5": 3.0,
        "carbon_monoxide": 0.1,
        "nitrogen_dioxide": 1.0,
        "sulphur_dioxide": 0.5,
        "ozone": 20.0,
    }
}


def test_get_air_quality_returns_cache(api):
    # Arrange
    api._cache_data("aqi_40.0_-74.0", {"cached": True})

    # Act
    with patch("requests.get") as mock_get:
        result = api.get_air_quality(40.0, -74.0)

    # Assert
    assert result == {"cached": True}
    mock_get.assert_not_called()


def test_get_air_quality_success(api):
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = AIR_QUALITY_PAYLOAD

        # Act
        result = api.get_air_quality(40.0, -74.0)

    # Assert
    assert result["aqi"] == 42
    assert result["category"] == "Good"


def test_get_air_quality_returns_empty_on_error(api):
    # Act
    with patch("requests.get", side_effect=Exception("boom")):
        result = api.get_air_quality(40.0, -74.0)

    # Assert
    assert result == {}


# --- condition / AQI mapping -----------------------------------------------


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
        (55, "Heavy Drizzle"),
        (56, "Light Freezing Drizzle"),
        (57, "Freezing Drizzle"),
        (61, "Light Rain"),
        (63, "Rain"),
        (65, "Heavy Rain"),
        (66, "Light Freezing Rain"),
        (67, "Freezing Rain"),
        (71, "Light Snow"),
        (73, "Snow"),
        (75, "Heavy Snow"),
        (77, "Snow Grains"),
        (80, "Light Showers"),
        (81, "Showers"),
        (82, "Heavy Showers"),
        (85, "Light Snow Showers"),
        (86, "Snow Showers"),
        (95, "Thunderstorm"),
        (96, "Thunderstorm with Light Hail"),
        (99, "Thunderstorm with Heavy Hail"),
        (999, "Unknown"),
    ],
)
def test_get_weather_condition_mapping(api, code, expected):
    # Assert
    assert api._get_weather_condition(code) == expected


@pytest.mark.parametrize(
    "aqi, expected",
    [
        (0, "Good"),
        (50, "Good"),
        (51, "Moderate"),
        (100, "Moderate"),
        (101, "Unhealthy for Sensitive Groups"),
        (150, "Unhealthy for Sensitive Groups"),
        (151, "Unhealthy"),
        (200, "Unhealthy"),
        (201, "Very Unhealthy"),
        (300, "Very Unhealthy"),
        (301, "Hazardous"),
        (999, "Hazardous"),
    ],
)
def test_get_aqi_category_boundaries(api, aqi, expected):
    # Assert
    assert api._get_aqi_category(aqi) == expected
