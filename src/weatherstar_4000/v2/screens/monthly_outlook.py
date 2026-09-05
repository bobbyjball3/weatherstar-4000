"""30-Day Monthly Outlook screen (port of legacy ``draw_monthly_outlook``).

Hardcoded temperature/precipitation outlook narrative reproduced verbatim from
the legacy simulator.
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
class MonthlyOutlookScreen(Screen):
    name = "monthly_outlook"
    media = ("backgrounds",)
    datasources = ()

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "4")
        render.draw_header(surface, ctx, "30-Day", "Outlook")

        colors = ctx.colors
        yellow = colors.get("yellow", _YELLOW)
        white = colors.get("white", _WHITE)

        now = datetime.now()
        month = now.strftime("%B %Y")
        y_pos = 120

        font_normal = _font(ctx, "normal")
        if font_normal is not None:
            title = font_normal.render(f"Outlook for {month}", True, yellow)
            surface.blit(title, title.get_rect(center=(320, y_pos)))
        y_pos += 35

        _blit(surface, ctx, "extended", "TEMPERATURE OUTLOOK", (60, y_pos), yellow)
        y_pos += 35

        _blit(
            surface,
            ctx,
            "normal",
            "Above Normal Temperatures Expected",
            (80, y_pos),
            white,
        )
        y_pos += 30

        _blit(surface, ctx, "small", "Probability: 60% above normal", (100, y_pos), white)
        y_pos += 40

        _blit(surface, ctx, "extended", "PRECIPITATION OUTLOOK", (60, y_pos), yellow)
        y_pos += 35

        _blit(
            surface,
            ctx,
            "normal",
            "Near Normal Precipitation Expected",
            (80, y_pos),
            white,
        )
        y_pos += 30

        _blit(surface, ctx, "small", "Probability: Equal chances", (100, y_pos), white)
        y_pos += 40

        font_small = _font(ctx, "small")
        if font_small is not None:
            source = font_small.render("Source: NOAA Climate Prediction Center", True, white)
            surface.blit(source, source.get_rect(center=(320, 380)))
