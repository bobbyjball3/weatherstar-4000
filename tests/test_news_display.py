"""Tests for the optimized news display module."""

from unittest.mock import patch

import pygame
import pytest

from weatherstar_4000.display_base import DisplayBase
from weatherstar_4000.news_display import NewsDisplay


@pytest.fixture(autouse=True)
def _reset_caches():
    DisplayBase._font_cache = {}
    yield


@pytest.fixture()
def news_display(display, screen):
    return NewsDisplay(screen)


def test_msn_headlines_returned(news_display):
    # Act
    headlines = news_display._get_msn_headlines()

    # Assert
    assert len(headlines) == 10
    assert all(isinstance(h, str) and isinstance(u, str) for h, u in headlines)


def test_msn_headlines_cached(news_display):
    # Act
    first = news_display._get_msn_headlines()
    second = news_display._get_msn_headlines()

    # Assert
    assert first is second


def test_reddit_headlines_returned(news_display):
    # Act
    headlines = news_display._get_reddit_headlines()

    # Assert
    assert len(headlines) == 10
    assert all(h.startswith("r/") for h, _ in headlines)


def test_local_headlines_include_city(news_display):
    # Act
    headlines = news_display._get_local_headlines("Springfield")

    # Assert
    assert any("Springfield" in h for h, _ in headlines)


def test_draw_msn_news_smoke(news_display):
    # Act
    news_display.draw_msn_news()


def test_draw_reddit_news_smoke(news_display):
    # Act
    news_display.draw_reddit_news()


def test_draw_local_news_smoke(news_display):
    # Act
    news_display.draw_local_news("Springfield")


def test_draw_local_news_default_city(news_display):
    # Act
    news_display.draw_local_news()


def test_scrolling_headlines_initializes_source(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    headlines = [("H1", "http://u")]

    # Act
    news_display._display_scrolling_headlines(headlines, "local")

    # Assert
    assert news_display.news_vertical_scroll["local"] == 200


def test_scrolling_headlines_advances_after_interval(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 100)
    news_display.news_vertical_scroll["local"] = 300
    headlines = [("H1", "http://u")]

    # Act
    news_display._display_scrolling_headlines(headlines, "local")

    # Assert
    assert news_display.news_vertical_scroll["local"] == 298


def test_scrolling_headlines_resets_when_scrolled_past(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 100)
    news_display.news_vertical_scroll["local"] = -10000

    # Act
    news_display._display_scrolling_headlines([("H1", "http://u")], "local")

    # Assert
    assert news_display.news_vertical_scroll["local"] == 400


def test_scrolling_headlines_tracks_clickable(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)

    # Act
    news_display._display_scrolling_headlines([("Headline One", "http://a")], "local")

    # Assert
    assert len(news_display.clickable_headlines) >= 1


def test_scrolling_headlines_no_clickable_without_url(news_display, monkeypatch):
    # Arrange
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)

    # Act
    news_display._display_scrolling_headlines([("No Link", "")], "local")

    # Assert
    assert news_display.clickable_headlines == []


@pytest.mark.parametrize(
    "text, max_width",
    [("short", 500), ("a very long headline that should definitely wrap somewhere", 120)],
)
def test_word_wrap_returns_nonempty_lines(news_display, text, max_width):
    # Act
    lines = news_display._word_wrap(text, max_width)

    # Assert
    assert lines
    assert " ".join(lines).replace("  ", " ") == text


def test_draw_colored_line_reddit(news_display):
    # Act
    news_display._draw_colored_line("r/news Test Story", 100, "reddit")


def test_draw_colored_line_reddit_tagged(news_display):
    # Act
    news_display._draw_colored_line("r/news [Tag] Story", 100, "reddit")


def test_draw_colored_line_msn(news_display):
    # Act
    news_display._draw_colored_line("Breaking: Big Story", 100, "msn")


def test_draw_colored_line_msn_update(news_display):
    # Act
    news_display._draw_colored_line("UPDATE: New Info", 100, "msn")


def test_draw_colored_line_msn_no_colon(news_display):
    # Act
    news_display._draw_colored_line("Plain msn line", 100, "msn")


def test_draw_colored_line_local_alert(news_display):
    # Act
    news_display._draw_colored_line("Emergency: Fire", 100, "local")


def test_draw_colored_line_local_no_colon(news_display):
    # Act
    news_display._draw_colored_line("Local line", 100, "local")


def test_draw_colored_line_default_source(news_display):
    # Act
    news_display._draw_colored_line("Anything", 100, "unknown")


def test_handle_click_hits_link(news_display):
    # Arrange
    news_display.clickable_headlines = [(pygame.Rect(0, 0, 50, 50), "http://example.com")]

    # Act
    with patch("webbrowser.open") as mock_open:
        result = news_display.handle_click((10, 10))

    # Assert
    assert result is True
    mock_open.assert_called_once_with("http://example.com")


def test_handle_click_misses_link(news_display):
    # Arrange
    news_display.clickable_headlines = [(pygame.Rect(0, 0, 10, 10), "http://example.com")]

    # Act
    result = news_display.handle_click((500, 500))

    # Assert
    assert result is False
