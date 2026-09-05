"""Boot/progress screen shown while the engine prepares data."""

from __future__ import annotations

from typing import Any, ClassVar

import pygame

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen


@plugin
class ProgressScreen(Screen):
    name = "progress"
    media = ("backgrounds",)

    status: ClassVar[str] = "Loading WeatherStar 4000..."

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "1")
        render.draw_header(surface, ctx, "WeatherStar", "4000")
        render.draw_centered_text(surface, ctx, self.status, 240, font_name="large")
        render.draw_centered_text(
            surface, ctx, "Retrieving current conditions and forecasts...", 300
        )
