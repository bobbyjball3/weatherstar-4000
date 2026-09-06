"""Boot/progress screen shown while the engine prepares data."""

from __future__ import annotations

from typing import Any, ClassVar

import pygame

from weatherstar.components.base import ComponentSpec
from weatherstar.registry import plugin
from weatherstar.screens.base import Screen
from weatherstar.themes import LayoutVariant


@plugin
class ProgressScreen(Screen):
    name = "progress"
    media = ("backgrounds",)
    variants = {
        LayoutVariant.WS4000: "compose_4000",
    }

    layout = (
        ComponentSpec(component="background", config={"background_name": "1"}),
        ComponentSpec(component="header", config={"title_top": "Weather Star", "title_bottom": ""}),
        ComponentSpec(component="clock"),
    )

    status: ClassVar[str] = ""

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        status = self.status or f"Loading {ctx.theme.title}..."
        self.centered(surface, ctx, status, 240, font_name="large")
        self.centered(surface, ctx, "Retrieving current conditions and forecasts...", 300)
