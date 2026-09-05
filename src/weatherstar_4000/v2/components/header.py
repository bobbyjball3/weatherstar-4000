"""Shared Component plugins.

These are reusable, named renderers the engine can compose into Screens via the
``components`` dependency list (see ``weatherstar_4000.v2.components`` package).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pygame
from pydantic import Field

from weatherstar_4000.v2.component import Component
from weatherstar_4000.v2.registry import plugin

if TYPE_CHECKING:
    from weatherstar_4000.v2.context import AppContext


@plugin
class Header(Component):
    """Standard screen header: corner logo, yellow title, NOAA mark, clock/date."""

    name = "header"

    title_top: str = Field(default="WeatherStar", description="Top line of the screen header.")
    title_bottom: str = Field(default="4000", description="Bottom line of the screen header.")
    has_noaa: bool = Field(
        default=False, description="Show the NOAA mark to the right of the header title."
    )

    def render(self, surface: pygame.Surface, ctx: AppContext) -> None:
        from weatherstar_4000.v2 import render

        render.draw_header(
            surface,
            ctx,
            self.title_top,
            self.title_bottom or None,
            has_noaa=self.has_noaa,
        )


@plugin
class Background(Component):
    """Fills the surface with a named background asset."""

    name = "background"

    background_name: str = Field(
        default="1", description="Background asset key to fill the screen (e.g. '1'..'6')."
    )

    def render(self, surface: pygame.Surface, ctx: AppContext) -> None:
        backgrounds = ctx.assets.get("backgrounds") or {}
        image = backgrounds.get(self.background_name)
        if image is None:
            image = next(iter(backgrounds.values()), None)
        if image is not None:
            surface.blit(image, (0, 0))
        else:
            surface.fill(ctx.colors["blue"])


@plugin
class Clock(Component):
    """Top-right live clock/date, matching the classic header look."""

    name = "clock"

    def render(self, surface: pygame.Surface, ctx: AppContext) -> None:
        fonts = ctx.fonts
        colors = ctx.colors
        small = fonts.get("small", fonts.get("title"))
        now = datetime.now()
        time_text = small.render(now.strftime("%I:%M %p").lstrip("0"), True, colors["white"])
        date_text = small.render(now.strftime("%a %b %d").upper(), True, colors["white"])
        time_rect = time_text.get_rect(right=surface.get_width() - 50, y=34)
        date_rect = date_text.get_rect(right=surface.get_width() - 50, y=54)
        surface.blit(time_text, time_rect)
        surface.blit(date_text, date_rect)
