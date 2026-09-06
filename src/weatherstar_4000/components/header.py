"""Header component: the standard screen header band.

Draws the corner logo, yellow two-line title, and optional NOAA mark.  The
top-right live clock/date is intentionally drawn by the sibling ``clock``
component so a screen can compose ``header`` + ``clock`` (matching the classic
``render.draw_header`` look) or draw them independently.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pydantic import Field

from weatherstar_4000.components.base import Component
from weatherstar_4000.registry import plugin

if TYPE_CHECKING:
    from weatherstar_4000.context import AppContext


@plugin
class Header(Component):
    """Corner logo, yellow title, optional NOAA mark (clock drawn separately)."""

    name = "header"

    title_top: str = Field(default="WeatherStar", description="Top line of the screen header.")
    title_bottom: str = Field(
        default="",
        description=(
            "Bottom line of the screen header. When blank, the active theme's "
            "product line (e.g. '3000') is shown instead."
        ),
    )
    has_noaa: bool = Field(
        default=False, description="Show the NOAA mark to the right of the header title."
    )

    def render(self, surface: pygame.Surface, ctx: AppContext) -> None:
        from weatherstar_4000 import render

        bottom = self.title_bottom
        if not bottom:
            bottom = getattr(ctx.theme, "title_bottom", "") or None
        render.draw_header(
            surface,
            ctx,
            self.title_top,
            bottom,
            has_noaa=self.has_noaa,
            include_clock=False,
        )
