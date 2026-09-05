"""Boot/progress screen shown while the engine prepares data."""

from __future__ import annotations

from typing import Any, ClassVar

import pygame

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen


@plugin
class ProgressScreen(Screen):
    name = "progress"
    media = ("backgrounds",)
    layout = (
        ComponentSpec(component="background", config={"background_name": "1"}),
        ComponentSpec(
            component="header", config={"title_top": "WeatherStar", "title_bottom": "4000"}
        ),
        ComponentSpec(component="clock"),
    )

    status: ClassVar[str] = "Loading WeatherStar 4000..."

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        self.centered(surface, ctx, self.status, 240, font_name="large")
        self.centered(surface, ctx, "Retrieving current conditions and forecasts...", 300)
