"""Weather Records screen (port of legacy ``draw_weather_records``).

Hardcoded record table for "this day" plus a "This Day in Weather History"
note, reproduced verbatim from the legacy simulator.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

_WHITE = (255, 255, 255)
_YELLOW = (255, 255, 0)


def _font(ctx: Any, key: str) -> pygame.font.Font | None:
    font = ctx.fonts.get(key)
    if font is None and ctx.fonts:
        font = next(iter(ctx.fonts.values()))
    return font


def _blit(surface: pygame.Surface, ctx: Any, font_key: str, text: str, pos, color) -> None:
    font = _font(ctx, font_key)
    if font is None:
        return
    surface.blit(font.render(text, True, color), pos)


@plugin
class WeatherRecordsScreen(Screen):
    name = "weather_records"
    media = ("backgrounds",)
    datasources = ()

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "4")
        render.draw_header(surface, ctx, "Weather", "Records")

        colors = ctx.colors
        yellow = colors.get("yellow", _YELLOW)
        white = colors.get("white", _WHITE)

        now = datetime.now()
        date_str = now.strftime("%B %d")
        y_pos = 120

        font_normal = _font(ctx, "normal")
        if font_normal is not None:
            title = font_normal.render(f"Records for {date_str}", True, yellow)
            surface.blit(title, title.get_rect(center=(320, y_pos)))
        y_pos += 40

        records = [
            ("Record High", "92\u00b0F (1998)"),
            ("Record Low", "41\u00b0F (1965)"),
            ("Average High", "75\u00b0F"),
            ("Average Low", "58\u00b0F"),
            ("Record Rainfall", '3.21" (1977)'),
            ("Record Snowfall", '0.0" (Never)'),
        ]

        for label, value in records:
            _blit(surface, ctx, "normal", f"{label}:", (120, y_pos), white)
            _blit(surface, ctx, "normal", value, (350, y_pos), yellow)
            y_pos += 35

        y_pos += 20
        _blit(surface, ctx, "extended", "THIS DAY IN WEATHER HISTORY", (60, y_pos), yellow)
        y_pos += 35

        history_text = "1992: Hurricane Andrew made landfall in Florida"
        _blit(surface, ctx, "small", history_text, (80, y_pos), white)
