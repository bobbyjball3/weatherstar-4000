"""Tests for the weatherstar settings manager."""

import json

import pytest

from weatherstar_4000 import weatherstar_settings

DEFAULT_DISPLAY_VOLUME = 0.3


@pytest.fixture()
def settings_file(tmp_path, monkeypatch):
    """Point the module at a temp settings file."""
    path = tmp_path / "settings.json"
    monkeypatch.setattr(weatherstar_settings, "SETTINGS_FILE", path)
    return path


def test_load_settings_returns_defaults_when_missing(settings_file):
    # Act
    settings = weatherstar_settings.load_settings()

    # Assert
    assert settings["location"]["auto_detect"] is True
    assert settings["location"]["lat"] is None
    assert settings["display"]["music_volume"] == DEFAULT_DISPLAY_VOLUME
    assert settings["display"]["show_marine"] is False


def test_load_settings_merges_partial_saved_settings(settings_file):
    # Arrange
    settings_file.write_text(json.dumps({"display": {"music_volume": 0.7}}))

    # Act
    settings = weatherstar_settings.load_settings()

    # Assert
    assert settings["display"]["music_volume"] == 0.7
    assert settings["location"]["auto_detect"] is True


def test_load_settings_preserves_unknown_saved_keys(settings_file):
    # Arrange
    settings_file.write_text(json.dumps({"display": {"custom": "value"}}))

    # Act
    settings = weatherstar_settings.load_settings()

    # Assert
    assert settings["display"]["custom"] == "value"


def test_load_settings_returns_defaults_on_corrupt_json(settings_file):
    # Arrange
    settings_file.write_text("{not valid json")

    # Act
    settings = weatherstar_settings.load_settings()

    # Assert
    assert settings["location"]["auto_detect"] is True


def test_save_settings_writes_file(settings_file):
    # Act
    result = weatherstar_settings.save_settings({"display": {"music_volume": 0.5}})

    # Assert
    assert result is True
    assert json.loads(settings_file.read_text())["display"]["music_volume"] == 0.5


def test_save_settings_returns_false_on_error(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr(weatherstar_settings, "SETTINGS_FILE", tmp_path / "no" / "dir" / "f.json")

    # Act
    result = weatherstar_settings.save_settings({"a": 1})

    # Assert
    assert result is False


def test_save_and_load_round_trip(settings_file):
    # Act
    weatherstar_settings.save_location(40.7128, -74.0060, "New York, NY", False)

    # Assert
    location = weatherstar_settings.get_saved_location()
    assert location == (40.7128, -74.0060, "New York, NY")


@pytest.mark.parametrize(
    "saved_location, expected",
    [
        ({"auto_detect": True, "lat": 40.7, "lon": -74.0}, None),
        ({"auto_detect": False, "lat": None, "lon": -74.0}, None),
        ({"auto_detect": False, "lat": 0, "lon": -74.0}, None),
        ({"auto_detect": False, "lat": 40.7, "lon": 0}, None),
        # Description key absent: get_saved_location returns None for it.
        ({"auto_detect": False, "lat": 40.7, "lon": -74.0}, (40.7, -74.0, None)),
        (
            {"auto_detect": False, "lat": 40.7, "lon": -74.0, "description": "NYC"},
            (40.7, -74.0, "NYC"),
        ),
    ],
)
def test_get_saved_location_variants(settings_file, saved_location, expected):
    # Arrange
    settings = weatherstar_settings.load_settings()
    settings["location"] = saved_location
    weatherstar_settings.save_settings(settings)

    # Act
    result = weatherstar_settings.get_saved_location()

    # Assert
    assert result == expected


def test_save_location_generates_description_when_omitted(settings_file):
    # Act
    weatherstar_settings.save_location(lat=34.0522, lon=-118.2437, auto_detect=False)

    # Assert
    settings = weatherstar_settings.load_settings()
    assert settings["location"]["description"] == "34.0522, -118.2437"


def test_save_display_preferences_merges_into_existing(settings_file):
    # Act
    weatherstar_settings.save_display_preferences({"music_volume": 0.7, "show_marine": True})

    # Assert
    prefs = weatherstar_settings.get_display_preferences()
    assert prefs["music_volume"] == 0.7
    assert prefs["show_marine"] is True
    assert "show_trends" in prefs


def test_get_display_preferences_returns_defaults(settings_file):
    # Act
    prefs = weatherstar_settings.get_display_preferences()

    # Assert
    assert isinstance(prefs, dict)
    assert prefs["music_volume"] == DEFAULT_DISPLAY_VOLUME
