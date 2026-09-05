"""Tests for the color theme module."""

import pytest

from weatherstar_4000.themes import (
    AMBER_THEME,
    AVAILABLE_THEMES,
    CLASSIC_THEME,
    DARK_THEME,
    HIGH_CONTRAST_THEME,
    RETRO_GREEN_THEME,
    ColorTheme,
    get_theme,
    list_themes,
)

ALL_THEMES = [
    CLASSIC_THEME,
    DARK_THEME,
    HIGH_CONTRAST_THEME,
    RETRO_GREEN_THEME,
    AMBER_THEME,
]


def test_color_theme_stores_name_and_colors():
    # Act
    theme = ColorTheme("Test", {"white": (1, 2, 3)})

    # Assert
    assert theme.name == "Test"
    assert theme.get_color("white") == (1, 2, 3)


def test_get_color_returns_white_fallback_for_unknown_key():
    # Arrange
    theme = ColorTheme("Test", {"white": (9, 9, 9)})

    # Assert
    assert theme.get_color("missing") == (255, 255, 255)


@pytest.mark.parametrize(
    "theme_name",
    ["classic", "dark", "high_contrast", "retro_green", "amber"],
)
def test_get_theme_returns_named_theme(theme_name):
    # Assert
    assert get_theme(theme_name) is AVAILABLE_THEMES[theme_name]


def test_get_theme_unknown_name_falls_back_to_classic():
    # Assert
    assert get_theme("does-not-exist") is CLASSIC_THEME


def test_list_themes_matches_registry():
    # Assert
    assert sorted(list_themes()) == sorted(AVAILABLE_THEMES.keys())


@pytest.mark.parametrize(
    "theme, key",
    [
        (theme, key)
        for theme in ALL_THEMES
        for key in ["yellow", "white", "black", "purple_header", "light_blue", "cyan", "red"]
    ],
)
def test_theme_defines_required_color_keys(theme, key):
    # Assert
    assert key in theme.colors


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_theme_colors_are_valid_rgb(theme):
    # Assert
    for name, color in theme.colors.items():
        assert len(color) == 3, f"{theme.name} color {name} is not RGB"
        assert all(0 <= channel <= 255 for channel in color), f"{theme.name} {name}: {color}"


def test_all_registered_themes_have_names():
    # Assert
    for theme in AVAILABLE_THEMES.values():
        assert theme.name
