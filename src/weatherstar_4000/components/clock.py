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
        small = self.font(ctx, "small")
        colors = ctx.colors
        now = datetime.now()
        time_text = small.render(now.strftime("%I:%M %p").lstrip("0"), True, colors["white"])
        date_text = small.render(now.strftime("%a %b %d").upper(), True, colors["white"])
        time_rect = time_text.get_rect(right=surface.get_width() - 50, y=34)
        date_rect = date_text.get_rect(right=surface.get_width() - 50, y=54)
        surface.blit(time_text, time_rect)
        surface.blit(date_text, date_rect)
