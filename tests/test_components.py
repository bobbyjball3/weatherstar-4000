"""Tests for shared Component plugins."""

import pygame

from weatherstar.components.background import Background
from weatherstar.components.clock import Clock
from weatherstar.components.header import Header
from weatherstar.context import AppContext, DataRegistry, Location


def _ctx(surface, *, assets=None):
    fonts = {
        "small": pygame.font.Font(None, 20),
        "title": pygame.font.Font(None, 32),
    }
    return AppContext(
        surface=surface,
        fonts=fonts,
        assets=assets or {},
        data=DataRegistry(),
        location=Location(lat=28.0, lon=-81.0),
    )


def test_header_renders(screen):
    ctx = _ctx(screen)
    Header().render(screen, ctx)
    colors_on_screen = {
        screen.get_at((x, y))[:3] for x in range(170, 300, 10) for y in range(30, 55)
    }
    assert ctx.colors["yellow"] in colors_on_screen


def test_background_fills_fallback_color(screen):
    ctx = _ctx(screen)
    Background().render(screen, ctx)
    assert screen.get_at((0, 0))[:3] == ctx.colors["blue"]


def test_background_uses_asset_when_present(screen):
    background = pygame.Surface((10, 10))
    background.fill((10, 20, 30))
    ctx = _ctx(screen, assets={"backgrounds": {"1": background}})
    Background().render(screen, ctx)
    assert screen.get_at((0, 0))[:3] == (10, 20, 30)


def test_clock_renders_text(screen):
    ctx = _ctx(screen)
    Clock().render(screen, ctx)
    band = [screen.get_at((x, y))[:3] for x in range(480, 640, 5) for y in range(30, 70, 5)]
    assert ctx.colors["white"] in band
