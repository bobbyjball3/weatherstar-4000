"""Clock component: top-right live clock/date, matching the classic header look."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pygame

from weatherstar_4000.components.base import Component
from weatherstar_4000.registry import plugin

if TYPE_CHECKING:
    from weatherstar_4000.context import AppContext


@plugin
class Clock(Component):
    """Top-right live clock/date, matching the classic header look."""

    name = "clock"

    def render(self, surface: pygame.Surface, ctx: AppContext) -> None:
        # The 3000 look moves the clock into the bottom scroll band; the theme
        # hides the top-right clock with a per-screen "show_clock" token.
        if not ctx.layout("show_clock", True):
            return
        from weatherstar_4000.renderer import blit_text_shadowed

        small = self.font(ctx, "small")
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        date_str = now.strftime("%a %b %d").upper()
        color = ctx.colors["white"]
        time_rect = small.render(time_str, True, color).get_rect(
            right=surface.get_width() - 50, y=34
        )
        date_rect = small.render(date_str, True, color).get_rect(
            right=surface.get_width() - 50, y=54
        )
        blit_text_shadowed(surface, ctx, small, time_str, color, time_rect)
        blit_text_shadowed(surface, ctx, small, date_str, color, date_rect)
