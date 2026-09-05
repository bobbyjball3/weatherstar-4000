"""Tests for the simulated local news fetcher."""

from unittest.mock import patch

from weatherstar_4000 import get_local_news


def test_get_local_news_by_location_returns_headline_tuples():
    # Act
    headlines = get_local_news.get_local_news_by_location(40.0, -74.0)

    # Assert
    assert isinstance(headlines, list)
    assert len(headlines) > 0
    for headline, url in headlines:
        assert isinstance(headline, str)
        assert isinstance(url, str)
        assert url.startswith("https://")


def test_get_city_name_city_and_state():
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"address": {"city": "New York", "state": "NY"}}

        # Assert
        assert get_local_news.get_city_name_from_coords(40.7, -74.0) == "New York, NY"


def test_get_city_name_town_without_state():
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"address": {"village": "Smallville"}}

        # Assert
        assert get_local_news.get_city_name_from_coords(40.0, -74.0) == "Smallville"


def test_get_city_name_defaults_when_no_city():
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"address": {}}

        # Assert
        assert get_local_news.get_city_name_from_coords(0.0, 0.0) == "Local Area"


def test_get_city_name_defaults_on_bad_status():
    # Arrange
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500

        # Assert
        assert get_local_news.get_city_name_from_coords(0.0, 0.0) == "Local Area"


def test_get_city_name_defaults_on_exception():
    # Arrange
    with patch("requests.get", side_effect=Exception("down")):
        # Assert
        assert get_local_news.get_city_name_from_coords(0.0, 0.0) == "Local Area"
