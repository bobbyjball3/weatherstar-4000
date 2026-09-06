"""Shared pytest configuration and fixtures for Weather Star tests.

pygame is driven headlessly: SDL dummy drivers are forced before any pygame
import so rendering code can be exercised on CI machines without a display.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEO_WINDOW_POS", "0,0")

import pygame
import pytest

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Font names used by the display/rendering code.
FONT_NAMES = [
    "title",
    "large",
    "normal",
    "small",
    "tiny",
    "extended",
    "forecast",
    "scroller",
]


@pytest.fixture()
def pygame_env():
    """Initialize pygame with dummy SDL drivers, reset per test."""
    if not pygame.get_init():
        pygame.init()
    yield pygame
    pygame.quit()


@pytest.fixture()
def screen(pygame_env):
    """Return a plain dummy surface to draw onto."""
    return pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))


@pytest.fixture()
def display(pygame_env):
    """Set a dummy video mode so convert()/convert_alpha() work."""
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    yield pygame.display.get_surface()


@pytest.fixture()
def fonts(pygame_env):
    """Return a dict of real pygame fonts under the names display code uses."""
    return {name: pygame.font.Font(None, 20) for name in FONT_NAMES}
