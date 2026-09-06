"""Marine / Beach Forecast screen.

The legacy display shows hardcoded coastal conditions; that literal content is
reproduced here verbatim (values rendered yellow when they flag severity).
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar.components.base import ComponentSpec
from weatherstar.registry import plugin
from weatherstar.screens.base import Screen
from weatherstar.themes import LayoutVariant

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


@plugin
class MarineForecastScreen(Screen):
    name = "marine_forecast"
    media = ("backgrounds", "fonts", "logos")

    variants = {
        LayoutVariant.WS4000: "compose_4000",
    }

    layout = (
        ComponentSpec(component="background", config={"background_name": "3"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Marine", "title_bottom": "Forecast", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        yellow = self.color(ctx, "yellow", (255, 255, 0))
        white = self.color(ctx, "white", (255, 255, 255))
        normal = self.font(ctx, "normal")

        y_pos = 120
        title = self.font(ctx, "extended").render("COASTAL CONDITIONS", True, yellow)
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
