"""Tests for the news display module (smoke + caching logic)."""

from types import SimpleNamespace

import pytest

import weatherstar_4000.news_displays as nd
from weatherstar_4000.news_displays import WeatherStarNewsDisplays


@pytest.fixture()
def news_display(mock_ws):
    return WeatherStarNewsDisplays(mock_ws)


# --- get_cached_city_name --------------------------------------------------


def test_get_cached_city_name_uses_cache(news_display, monkeypatch):
    # Arrange
    news_display.ws.cached_city_name = "New York, NY"
    news_display.ws.city_name_cached_at = 1_000_000
    monkeypatch.setattr("time.time", lambda: 1_000_100)  # 100s later < 1h

    fake_news = SimpleNamespace(
        get_city_name_from_coords=lambda *a: (_ for _ in ()).throw(AssertionError)
    )
    monkeypatch.setattr(nd, "get_local_news", fake_news)

    # Act
    city = news_display.get_cached_city_name()

    # Assert
    assert city == "New York, NY"


def test_get_cached_city_name_expired_fetches(news_display, monkeypatch):
    # Arrange
    news_display.ws.cached_city_name = "Stale City"
    news_display.ws.city_name_cached_at = 0
    monkeypatch.setattr("time.time", lambda: 1_000_000)

    fake_news = SimpleNamespace(get_city_name_from_coords=lambda lat, lon: "Springfield, MO")
    monkeypatch.setattr(nd, "get_local_news", fake_news)

    # Act
    city = news_display.get_cached_city_name()

    # Assert
    assert city == "Springfield, MO"
    assert news_display.ws.cached_city_name == "Springfield, MO"
    assert news_display.ws.city_name_cached_at == 1_000_000


def test_get_cached_city_name_fetches_when_none(news_display, monkeypatch):
    # Arrange
    news_display.ws.cached_city_name = None
    monkeypatch.setattr("time.time", lambda: 1_000_000)

    fake_news = SimpleNamespace(get_city_name_from_coords=lambda lat, lon: "Tulsa, OK")
    monkeypatch.setattr(nd, "get_local_news", fake_news)

    # Act
    city = news_display.get_cached_city_name()

    # Assert
    assert city == "Tulsa, OK"


# --- draw methods ----------------------------------------------------------


def test_draw_msn_news(news_display):
    # Act
    news_display.draw_msn_news()


def test_draw_reddit_news(news_display):
    # Act
    news_display.draw_reddit_news()


def test_draw_local_news(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr(news_display, "get_cached_city_name", lambda: "Springfield")
    fake_news = SimpleNamespace(
        get_local_news_by_location=lambda lat, lon: [("Local headline", "http://x")],
        get_city_name_from_coords=lambda *a: "Springfield",
    )
    monkeypatch.setattr(nd, "get_local_news", fake_news)

    # Act
    news_display.draw_local_news()


def test_draw_local_news_falls_back_to_simulated(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr(news_display, "get_cached_city_name", lambda: "Springfield")
    import weatherstar_4000.get_local_news_real as real

    def boom(lat, lon):
        raise RuntimeError("real news down")

    monkeypatch.setattr(real, "get_local_news_by_location", boom)
    fake_news = SimpleNamespace(
        get_local_news_by_location=lambda lat, lon: [("Fallback headline", "http://y")],
        get_city_name_from_coords=lambda *a: "Springfield",
    )
    monkeypatch.setattr(nd, "get_local_news", fake_news)

    # Act
    news_display.draw_local_news()


# --- display helpers -------------------------------------------------------


def test_display_scrolling_headlines_initializes(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 0.0)

    # Act
    news_display._display_scrolling_headlines([("Hello", "http://u")], "local")

    # Assert
    assert news_display.ws.news_vertical_scroll["local"] == 0


def test_display_scrolling_headlines_truncates_and_tracks(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 0.0)
    long_text = "x" * 300

    # Act
    news_display._display_scrolling_headlines([(long_text, "http://u")], "local")

    # Assert
    assert len(news_display.ws.clickable_headlines) >= 1
    assert news_display.ws.clickable_headlines[0]["url"] == "http://u"


def test_display_scrolling_headlines_colors_by_source(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 0.0)

    # Act
    for source in ["reddit", "local", "msn"]:
        news_display.ws.news_vertical_scroll = {}
        news_display._display_scrolling_headlines([("headline", "http://u")], source)


def test_display_categorized_headlines(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 0.0)
    headlines = [
        ("[BREAKING]", "Major storm approaching", "http://msn/1"),
        ("r/news", "Some reddit story", "http://reddit/1"),
        ("[TECH]", "Apple product", "http://msn/2"),
    ]

    # Act
    news_display._display_categorized_headlines(headlines, "msn")

    # Assert
    assert len(news_display.ws.clickable_headlines) >= 3


def test_display_categorized_headlines_empty_entries(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 0.0)

    # Act
    news_display._display_categorized_headlines([("", "", "")], "msn")
