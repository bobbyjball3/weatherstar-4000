"""Travel Cities screen: static grid of major US city weather."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

_FONT_SIZES = {
    "title": 32,
    "large": 32,
    "extended": 32,
    "small": 28,
    "normal": 20,
    "forecast": 24,
    "tiny": 16,
    "scroller": 24,
}


def _ensure_fonts(ctx: Any) -> None:
    fonts = getattr(ctx, "fonts", None)
    if not isinstance(fonts, dict):
        return
    for name, size in _FONT_SIZES.items():
        fonts.setdefault(name, pygame.font.Font(None, size))


def _font(ctx: Any, name: str) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None)
    if isinstance(fonts, dict):
        found = fonts.get(name)
        if found is not None:
            return found
    return pygame.font.Font(None, _FONT_SIZES.get(name, 20))


def _color(
    ctx: Any, key: str, fallback: tuple[int, int, int] = (255, 255, 255)
) -> tuple[int, int, int]:
    try:
        return (ctx.colors or {}).get(key, fallback)
    except Exception:
        return fallback


@plugin
class TravelCitiesScreen(Screen):
    name = "travel_cities"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ()

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        _ensure_fonts(ctx)
        render.draw_background(surface, ctx, "5")
        render.draw_header(surface, ctx, "Travel Cities", "Weather")

        cities = [
            ("NEW YORK", 72, "Partly Cloudy"),
            ("LOS ANGELES", 78, "Sunny"),
            ("CHICAGO", 65, "Cloudy"),
            ("MIAMI", 85, "T-Storms"),
            ("DALLAS", 88, "Mostly Sunny"),
            ("SEATTLE", 62, "Rain"),
            ("DENVER", 70, "Clear"),
            ("ATLANTA", 79, "Partly Cloudy"),
        ]

        yellow = _color(ctx, "yellow")
        white = _color(ctx, "white")
        y_pos = 120

        for i, (city, temp, conditions) in enumerate(cities):
            if i % 2 == 1:
                bar_rect = pygame.Rect(60, y_pos - 5, 520, 30)
                pygame.draw.rect(surface, (0, 0, 60), bar_rect)

            city_surf = _font(ctx, "normal").render(city, True, yellow)
            surface.blit(city_surf, (80, y_pos))

            temp_surf = _font(ctx, "normal").render(f"{temp}\N{DEGREE SIGN}", True, white)
            surface.blit(temp_surf, (320, y_pos))

            cond_surf = _font(ctx, "normal").render(conditions, True, white)
            surface.blit(cond_surf, (400, y_pos))

            y_pos += 35
