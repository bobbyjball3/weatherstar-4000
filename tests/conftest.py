"""Shared pytest configuration and fixtures for WeatherStar 4000 tests.

pygame is driven headlessly: SDL dummy drivers are forced before any pygame
import so rendering code can be exercised on CI machines without a display.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEO_WINDOW_POS", "0,0")

from unittest.mock import MagicMock

import pygame
import pytest

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Font names used by the display classes.
FONT_NAMES = [
    "font_title",
    "font_large",
    "font_normal",
    "font_small",
    "font_tiny",
    "font_extended",
    "font_forecast",
    "font_scroller",
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


class _WSStub:
    """Stand-in for a WeatherStar instance used by display classes.

    Real instances get: a drawable ``screen``, real fonts and simple data
    containers. Any other attribute access falls back to a MagicMock so draw
    helpers (e.g. ``self.ws.draw_background(...)``) do not crash.
    """

    def __init__(self, screen, fonts):
        self.screen = screen
        self.weather_data = {}
        self.location = {}
        self.backgrounds = {}
        self.logos = {}
        self.icons = {}
        self.settings = {}
        self.scroller = MagicMock()
        # Scrolling/click state used by news displays.
        self.news_vertical_scroll = {}
        self.clickable_headlines = []
        self.last_news_scroll_time = 0.0
        # Location/caching state.
        self.lat = 40.7128
        self.lon = -74.0060
        self.cached_city_name = None
        self.city_name_cached_at = 0.0
        # Radar / trends / scrolling display state.
        self.radar_frames = []
        self.radar_frame_index = 0
        self.radar_last_update = 0.0
        self.radar_image = None
        self.weather_trends = {}
        self.health_scroll_pos = 0
        self.health_scroll_dir = 1
        for name, font in fonts.items():
            setattr(self, name, font)

    def _icon(self, *args, **kwargs):
        return pygame.Surface((32, 32))

    def __getattr__(self, name):
        if name == "icon_manager":
            manager = MagicMock()
            manager.get_icon = self._icon
            return manager
        return MagicMock()


@pytest.fixture()
def mock_ws(screen, fonts):
    """Return a WeatherStar stub with a real drawable screen and fonts."""
    return _WSStub(screen, fonts)


@pytest.fixture()
def ws_factory(screen, fonts):
    """Return a factory that builds a fresh WeatherStar stub per call."""

    def make():
        return _WSStub(screen, fonts)

    return make


class _FakeLogger:
    """Minimal stand-in for the weatherstar logger.

    The real WeatherStarLogger constructor calls ``pygame.quit()`` from its
    system-info probe, which would tear down pygame mid-test. Display classes
    fetch the logger through ``get_logger()``; as long as the module-global is
    already populated they never construct the real one.
    """

    def __init__(self):
        self.main_logger = MagicMock()
        self.api_logger = MagicMock()
        self.error_logger = MagicMock()

    def __getattr__(self, name):
        return MagicMock()

    def log_error(self, *args, **kwargs):
        pass

    def log_asset_load(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _inject_fake_logger():
    import weatherstar_4000.weatherstar_logger as wl

    wl.logger = _FakeLogger()
    yield
