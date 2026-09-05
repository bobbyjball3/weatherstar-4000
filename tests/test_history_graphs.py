"""Tests for the 30-day weather history data module."""

import time
from unittest.mock import patch

import pytest

from weatherstar_4000.history_graphs import WeatherHistory, get_weather_history


def _daily_response():
    return {
        "daily": {
            "time": ["2026-01-03", "2026-01-02", "2026-01-01"],
            "temperature_2m_max": [30, 20, 10],
            "temperature_2m_min": [20, 10, 0],
            "precipitation_sum": [0.5, None, 0],
        }
    }


def test_initial_state():
    # Act
    history = WeatherHistory()

    # Assert
    assert history.history_data["temperature"] == []
    assert history.history_data["precipitation"] == []
    assert history.cache_duration == 3600


def test_fetch_history_data_stores_all_days():
    # Arrange
    history = WeatherHistory()
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = _daily_response()

        # Act
        result = history.fetch_history_data(40.0, -74.0)

    # Assert
    assert result is True
    assert history.history_data["temperature"] == [
        ("2026-01-01", 10, 0),
        ("2026-01-02", 20, 10),
        ("2026-01-03", 30, 20),
    ]
    assert history.history_data["precipitation"] == [
        ("2026-01-01", 0),
        ("2026-01-02", 0),
        ("2026-01-03", 0.5),
    ]


def test_fetch_history_data_returns_true_even_with_empty_daily(monkeypatch, capsys):
    # Arrange
    history = WeatherHistory()
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}

        # Act
        result = history.fetch_history_data(40.0, -74.0)

    # Assert
    assert result is True
    assert history.history_data["temperature"] == []


def test_fetch_history_data_returns_false_on_bad_status():
    # Arrange
    history = WeatherHistory()
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500

        # Act
        result = history.fetch_history_data(40.0, -74.0)

    # Assert
    assert result is False


def test_fetch_history_data_returns_false_on_exception(capsys):
    # Arrange
    history = WeatherHistory()

    # Act
    with patch("requests.get", side_effect=Exception("boom")):
        result = history.fetch_history_data(40.0, -74.0)

    # Assert
    assert result is False
    assert "boom" in capsys.readouterr().out


def test_fetch_history_data_serves_from_cache(monkeypatch):
    # Arrange
    history = WeatherHistory()
    history.history_data["temperature"] = [("2026-01-01", 10, 0)]
    history.cache_time = time.time()

    # Act
    with patch("requests.get") as mock_get:
        result = history.fetch_history_data(40.0, -74.0)

    # Assert
    assert result is True
    mock_get.assert_not_called()


def test_fetch_history_data_cache_miss_when_empty_returns_false(monkeypatch):
    # Arrange
    history = WeatherHistory()
    history.cache_time = time.time()

    # Act
    with patch("requests.get") as mock_get:
        result = history.fetch_history_data(40.0, -74.0)

    # Assert
    assert result is False
    mock_get.assert_not_called()


def test_update_scroll_waits_during_delay():
    # Arrange
    history = WeatherHistory()
    history.last_scroll_time = time.time()

    # Act
    history.update_scroll(current_time=time.time(), scroll_speed=20)

    # Assert
    assert history.scroll_offset_temp == 0
    assert history.scroll_offset_precip == 0


def test_update_scroll_advances_after_delay():
    # Arrange
    history = WeatherHistory()
    history.last_scroll_time = time.time() - 10

    # Act
    history.update_scroll(current_time=time.time(), scroll_speed=20)

    # Assert
    expected = 20 * (1 / 60)
    assert history.scroll_offset_temp == pytest.approx(expected)
    assert history.scroll_offset_precip == pytest.approx(expected)


def test_get_weather_history_is_singleton():
    # Assert
    assert get_weather_history() is get_weather_history()
