"""Marine / Beach Forecast screen.

The legacy display shows hardcoded coastal conditions; that literal content is
reproduced here verbatim (values rendered yellow when they flag severity).
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

#: Literal (label, value) rows ported from ``displays.py::draw_marine_forecast``.
MARINE_CONDITIONS: list[tuple[str, str]] = [
    ("Water Temperature", "72\u00b0F"),
    ("Wave Height", "2-4 ft"),
    ("Wave Period", "6 seconds"),
    ("Rip Current Risk", "MODERATE"),
    ("UV Index", "8 (Very High)"),
    ("Tide", "High @ 2:30 PM"),
    ("Wind", "E 10-15 mph"),
    ("Visibility", "10+ miles"),
]

#: Value fragments that should draw in warning yellow.
_HIGHLIGHT_FRAGMENTS = ("MODERATE", "High")


def _font(ctx: Any, name: str, size: int) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None) or {}
    return fonts.get(name) or pygame.font.Font(None, size)


def _color(ctx: Any, key: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
    colors = getattr(ctx, "colors", None) or {}
    return colors.get(key, default)


@plugin
class MarineForecastScreen(Screen):
    name = "marine_forecast"
    media = ("backgrounds", "fonts", "logos")

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "3")
        render.draw_header(surface, ctx, "Marine", "Forecast")

        yellow = _color(ctx, "yellow", (255, 255, 0))
        white = _color(ctx, "white", (255, 255, 255))
        normal = _font(ctx, "normal", 20)

        y_pos = 120
        title = _font(ctx, "extended", 24).render("COASTAL CONDITIONS", True, yellow)
        surface.blit(title, (60, y_pos))
        y_pos += 35

        for label, value in MARINE_CONDITIONS:
            label_text = normal.render(f"{label}:", True, white)
            surface.blit(label_text, (80, y_pos))

            highlighted = any(fragment in value for fragment in _HIGHLIGHT_FRAGMENTS)
            color = yellow if highlighted else white
            value_text = normal.render(value, True, color)
            surface.blit(value_text, (300, y_pos))
            y_pos += 28
