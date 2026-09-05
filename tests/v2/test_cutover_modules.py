"""Tests for the self-contained v2 modules that replaced legacy dependencies."""

import time

import pygame

from weatherstar_4000.v2.datasources.history import HistoryDatasource
from weatherstar_4000.v2.datasources.news import LocalNewsDatasource
from weatherstar_4000.v2.media.icons import IconManager

_DAILY = {
    "time": ["2026-09-01", "2026-09-02", "2026-09-03"],
    "temperature_2m_max": [88.0, 90.0, 92.0],
    "temperature_2m_min": [70.0, 71.0, 72.0],
    "precipitation_sum": [0.0, 0.25, 0.0],
}


def test_history_temperature_returns_most_recent_first(monkeypatch):
    ds = HistoryDatasource()
    monkeypatch.setattr(ds, "http_get_json", lambda *a, **k: {"daily": dict(_DAILY)})
    rows = ds.temperature(28.5, -81.4)
    assert rows == [
        ("2026-09-03", 92.0, 72.0),
        ("2026-09-02", 90.0, 71.0),
        ("2026-09-01", 88.0, 70.0),
    ]


def test_history_precipitation_most_recent_first(monkeypatch):
    ds = HistoryDatasource()
    monkeypatch.setattr(ds, "http_get_json", lambda *a, **k: {"daily": dict(_DAILY)})
    rows = ds.precipitation(28.5, -81.4)
    assert rows == [("2026-09-03", 0.0), ("2026-09-02", 0.25), ("2026-09-01", 0.0)]


def test_history_refresh_false_when_empty(monkeypatch):
    ds = HistoryDatasource()
    monkeypatch.setattr(ds, "http_get_json", lambda *a, **k: {"daily": {}})
    assert ds.refresh(1.0, 2.0) is False


def test_history_scroll_offsets_advance_after_delay():
    ds = HistoryDatasource()
    assert ds.scroll_offsets == (0.0, 0.0)
    ds.scroll(time.time() + 5.0)
    temp_offset, precip_offset = ds.scroll_offsets
    assert temp_offset > 0.0
    assert precip_offset > 0.0


def test_local_news_headlines_are_cached(monkeypatch):
    ds = LocalNewsDatasource()
    first = ds.headlines(28.5, -81.4)
    assert first and all(len(item) == 2 for item in first)
    assert first[0][1].startswith("https://")
    assert ds.headlines(28.5, -81.4) == first


def test_local_news_city_name_empty_string():
    ds = LocalNewsDatasource()
    assert ds.city_name(28.5, -81.4) == ""


def test_icon_manager_returns_scaled_and_named(pygame_env, tmp_path):
    icon_dir = tmp_path / "icons"
    icon_dir.mkdir()
    surface = pygame.Surface((10, 10))
    surface.fill((255, 255, 255))
    pygame.image.save(surface, str(icon_dir / "Partly-Cloudy.png"))

    manager = IconManager(icon_dir)
    got = manager.get_icon("Partly-Cloudy", width=40, height=30)
    assert got is not None and got.get_size() == (40, 30)
    # Case-insensitive lookup for a different casing.
    assert manager.get_icon("partly-cloudy") is not None
    assert manager.get_icon("missing-icon") is None


def test_icon_manager_empty_directory(pygame_env, tmp_path):
    manager = IconManager(tmp_path)
    assert manager.get_icon("anything") is None
