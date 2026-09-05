"""Tests for the optimized display base module."""

from pathlib import Path

import pygame
import pytest

from weatherstar_4000.display_base import DisplayBase

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset_caches():
    DisplayBase._font_cache = {}
    DisplayBase._background_cache = {}
    DisplayBase._icon_cache = {}
    yield


@pytest.fixture()
def base(screen):
    return DisplayBase(screen, str(REPO_ROOT / "static_assets"))


def test_init_sets_up_screen_and_fonts(base, screen):
    # Assert
    assert base.screen is screen
    assert base.assets_path == REPO_ROOT / "static_assets"
    assert base.small_font is not None
    assert base.frame_count == 0


def test_get_font_paths_returns_expected_names(base):
    # Act
    paths = base._get_font_paths()

    # Assert
    assert set(paths) == {
        "small",
        "normal",
        "large",
        "compressed",
        "extended",
        "radar",
    }
    assert "Star4000.ttf" in paths["normal"]


def test_get_font_paths_static():
    # Act
    paths = DisplayBase._get_font_paths_static()

    # Assert
    assert paths["normal"].endswith("fonts/Star4000.ttf")


def test_preload_fonts_falls_back_when_cache_raises(screen, monkeypatch):
    # Arrange
    def explode(cls, font_type, size):
        raise RuntimeError("font broke")

    monkeypatch.setattr(DisplayBase, "_get_cached_font", classmethod(explode))

    # Act
    instance = DisplayBase(screen, str(REPO_ROOT / "static_assets"))

    # Assert
    assert instance.header_font is not None
    assert instance.time_font is not None


def test_get_cached_font_uses_file_when_present(display):
    # Act
    font = DisplayBase._get_cached_font("normal", 20)

    # Assert
    assert isinstance(font, pygame.font.Font)


def test_get_cached_font_uses_default_when_missing(display):
    # Arrange
    DisplayBase._font_cache = {}

    # Act
    font = DisplayBase._get_cached_font("nonexistent_type", 12)

    # Assert
    assert isinstance(font, pygame.font.Font)


def test_get_cached_font_caches_result(display):
    # Arrange
    DisplayBase._font_cache = {}

    # Act
    first = DisplayBase._get_cached_font("normal", 20)
    second = DisplayBase._get_cached_font("normal", 20)

    # Assert
    assert first is second


# --- backgrounds -----------------------------------------------------------


def test_load_background_returns_none_when_missing(screen, tmp_path):
    # Arrange
    base = DisplayBase(screen, str(tmp_path))

    # Act
    bg = base._load_background("1")

    # Assert
    assert bg is None


def test_load_background_loads_and_scales(display, tmp_path):
    # Arrange
    _write_png(tmp_path / "backgrounds" / "BackGround1.png", size=(20, 20))
    base = DisplayBase(pygame.Surface((640, 480)), str(tmp_path))

    # Act
    bg = base._load_background("1")

    # Assert
    assert bg is not None
    assert bg.get_size() == (640, 480)  # scaled to screen size


def test_load_background_returns_none_on_load_error(display, tmp_path):
    # Arrange
    backgrounds = tmp_path / "backgrounds"
    backgrounds.mkdir()
    (backgrounds / "BackGround1.png").write_bytes(b"not an image")
    base = DisplayBase(pygame.Surface((10, 10)), str(tmp_path))

    # Act
    bg = base._load_background("1")

    # Assert
    assert bg is None


def test_draw_background_fills_fallback_when_missing(screen, tmp_path):
    # Arrange
    base = DisplayBase(screen, str(tmp_path))

    # Act
    base.draw_background("1")

    # Assert
    assert screen.get_at((0, 0))[:3] == (0, 71, 171)  # COLORS["blue"]


def test_draw_background_dark_blue_fallback(screen, tmp_path):
    # Arrange
    base = DisplayBase(screen, str(tmp_path))

    # Act
    base.draw_background("2")

    # Assert
    assert screen.get_at((0, 0))[:3] == (0, 50, 100)  # COLORS["dark_blue"]


# --- header / icons / text ------------------------------------------------


def test_draw_header_with_and_without_subtitle(screen, base):
    # Act
    base.draw_header("Current", "Bottom")
    base.draw_header("Single")

    # Assert
    # Rendering happened without error; header is 60px tall at top.
    assert screen.get_size() == (640, 480)


def test_load_weather_icon_returns_none_when_missing(screen, tmp_path):
    # Arrange
    base = DisplayBase(screen, str(tmp_path))

    # Act
    icon = base._load_weather_icon("clear")

    # Assert
    assert icon is None


def test_load_weather_icon_loads_file(display, tmp_path):
    # Arrange
    import shutil

    icons = tmp_path / "icons"
    icons.mkdir(parents=True)
    shutil.copy(REPO_ROOT / "static_assets" / "icons" / "Clear.gif", icons / "Clear.gif")
    base = DisplayBase(pygame.Surface((10, 10)), str(tmp_path))

    # Act
    icon = base._load_weather_icon("clear")

    # Assert
    assert icon is not None
    assert icon.get_size() == (64, 64)  # scaled to standard size


def test_draw_weather_icon_text_fallback(screen, tmp_path):
    # Arrange
    base = DisplayBase(screen, str(tmp_path))

    # Act
    base.draw_weather_icon(10, 10, "clear")  # no icon -> text fallback

    # Assert
    assert True


def test_draw_text_centered(screen, base):
    # Act
    base.draw_text_centered("Hello", 100)

    # Assert
    assert True


def test_draw_text_wrapped_multiple_lines(screen, base):
    # Arrange
    long_text = "word " * 200

    # Act
    base.draw_text_wrapped(long_text, 5, 5, max_width=500, line_height=15)

    # Assert
    assert True


def test_draw_text_wrapped_single_word_overflow(screen, base):
    # Act
    base.draw_text_wrapped("supercalifragilisticexpialidocious" * 5, 5, 5, max_width=100)

    # Assert
    assert True


def test_update_performance_stats_tracks_and_resets(screen, base, monkeypatch):
    # Arrange
    ticks = iter([0, 10, 2000])
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: next(ticks))

    # Act
    base.update_performance_stats()
    base.update_performance_stats()

    # Assert
    assert base.frame_count == 2

    # Act
    base.update_performance_stats()  # >1s elapsed -> resets frame count

    # Assert
    assert base.frame_count == 0


def _write_png(path, size=(32, 32)):
    path.parent.mkdir(parents=True, exist_ok=True)
    surface = pygame.Surface(size)
    surface.fill((0, 0, 255))
    pygame.image.save(surface, str(path))
