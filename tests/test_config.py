"""Tests for the weatherstar configuration module."""

import pytest

from weatherstar_4000.config import (
    COLORS,
    DISPLAY_DURATION_MS,
    FONT_SIZE_HEADER,
    FONT_SIZE_LARGE,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SCROLL_SPEED,
    DisplayMode,
)


def test_screen_dimensions():
    # Assert
    assert SCREEN_WIDTH == 640
    assert SCREEN_HEIGHT == 480


def test_display_timing():
    # Assert
    assert DISPLAY_DURATION_MS == 15000
    assert SCROLL_SPEED == 100


@pytest.mark.parametrize(
    "constant, expected",
    [
        (FONT_SIZE_SMALL, 16),
        (FONT_SIZE_NORMAL, 20),
        (FONT_SIZE_LARGE, 24),
        (FONT_SIZE_HEADER, 36),
    ],
)
def test_font_sizes(constant, expected):
    # Assert
    assert constant == expected


@pytest.mark.parametrize(
    "key",
    ["blue", "white", "yellow", "black", "gray", "green", "red", "cyan", "dark_blue", "orange"],
)
def test_colors_palette_defines_key(key):
    # Assert
    assert key in COLORS
    assert len(COLORS[key]) == 3
    assert all(isinstance(channel, int) for channel in COLORS[key])


def test_display_mode_is_an_enum_of_strings():
    # Assert
    for mode in DisplayMode:
        assert isinstance(mode.value, str)


def test_display_mode_values_are_unique():
    # Arrange
    values = [mode.value for mode in DisplayMode]

    # Assert
    assert len(values) == len(set(values))
