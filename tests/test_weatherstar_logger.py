"""Tests for the WeatherStar logging system."""

import logging

import pytest

import weatherstar_4000.weatherstar_logger as wl
from weatherstar_4000.weatherstar_logger import WeatherStarLogger


@pytest.fixture()
def logger(tmp_path):
    return WeatherStarLogger(log_dir=str(tmp_path / "logs"), log_level=logging.DEBUG)


def test_init_creates_log_files(logger):
    # Assert
    assert logger.main_log.exists()
    assert logger.api_log.exists()
    assert logger.error_log.exists()
    assert logger.system_log.exists()


def test_init_creates_latest_links(logger):
    # Assert
    latest = logger.log_dir / "weatherstar_latest.log"
    assert latest.exists() or latest.is_symlink()


def test_log_startup_writes_to_main_log(logger):
    # Act
    logger.log_startup(40.7128, -74.0060)

    # Assert
    content = logger.main_log.read_text()
    assert "WeatherStar 4000 Starting" in content
    assert "Location: 40.7128, -74.006" in content


def test_log_api_call_success(logger):
    # Act
    logger.log_api_call("http://weather", response_code=200)

    # Assert
    assert "Status: 200" in logger.api_log.read_text()


def test_log_api_call_error(logger):
    # Act
    logger.log_api_call("http://weather", error="timeout")

    # Assert
    assert "API Error" in logger.api_log.read_text()
    assert "API failed" in logger.error_log.read_text()


def test_log_weather_data_with_current(logger):
    # Act
    logger.log_weather_data(
        "current", {"temperature": {"value": 22}, "textDescription": "Partly Cloudy"}
    )

    # Assert
    assert "Current Weather" in logger.main_log.read_text()


def test_log_weather_data_none(logger):
    # Act
    logger.log_weather_data("current", None)

    # Assert
    assert "No data received" in logger.main_log.read_text()


def test_log_display_change(logger):
    # Act
    logger.log_display_change("radar", "hazards")

    # Assert
    assert "radar -> hazards" in logger.main_log.read_text()


def test_log_asset_load_success_and_failure(logger):
    # Act
    logger.log_asset_load("logo", "a.png", success=True)
    logger.log_asset_load("logo", "b.png", success=False)

    # Assert
    content = logger.main_log.read_text()
    assert "Asset Loaded" in content
    assert "Asset Failed" in content


def test_log_error_without_exception(logger):
    # Act
    logger.log_error("something broke")

    # Assert
    assert "something broke" in logger.error_log.read_text()


def test_log_error_with_exception(logger):
    # Arrange
    exc = None
    try:
        raise ValueError("boom")
    except ValueError as e:
        exc = e

        # Act
        logger.log_error("wrapped error", exception=exc)

    # Assert
    error_content = logger.error_log.read_text()
    assert "wrapped error" in error_content
    assert "Traceback" in error_content


def test_log_shutdown(logger):
    # Act
    logger.log_shutdown()

    # Assert
    assert "Shutting Down" in logger.main_log.read_text()


def test_get_log_summary(logger):
    # Act
    summary = logger.get_log_summary()

    # Assert
    assert summary["main_log"] == str(logger.main_log)
    assert summary["api_log"] == str(logger.api_log)
    assert summary["error_log"] == str(logger.error_log)
    assert summary["system_log"] == str(logger.system_log)


def test_system_log_contains_platform_info(logger):
    # Assert
    content = logger.system_log.read_text()
    assert '"python_version"' in content
    assert '"working_directory"' in content


def test_init_logger_and_get_logger_share_global(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr(wl, "logger", None)

    # Act
    created = wl.init_logger(log_dir=str(tmp_path / "logs"))

    # Assert
    assert created is wl.get_logger()


def test_get_logger_lazy_initializes(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr(wl, "logger", None)
    monkeypatch.setattr(
        WeatherStarLogger, "__init__", lambda self, *a, **k: setattr(self, "ok", True)
    )

    # Act
    instance = wl.get_logger()

    # Assert
    assert instance.ok is True
    assert wl.logger is instance
