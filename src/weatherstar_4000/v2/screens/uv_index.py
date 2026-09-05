"""UV Index Forecast screen (port of legacy ``draw_uv_index``).

Renders a DATE / UV INDEX / PROTECTION table from the ``uv_index`` datasource
rows, using the datasource's static protection-level classification.
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

_MAX_ROWS = 7


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


def _format_date(date_str: Any) -> str:
    if not date_str:
        return ""
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").strftime("%a %m/%d")
    except (TypeError, ValueError):
        return str(date_str)


@plugin
class UvIndexScreen(Screen):
    name = "uv_index"
    media = ("backgrounds",)
    datasources = ("uv_index",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "5")
        render.draw_header(surface, ctx, "UV Index", "Forecast")

        colors = ctx.colors
        yellow = colors.get("yellow", _YELLOW)
        white = colors.get("white", _WHITE)

        rows = self._daily_rows(ctx)
        if not rows:
            render.draw_centered_text(surface, ctx, "UV Index data unavailable", 240)
            return

        y_pos = 120
        _blit(surface, ctx, "normal", "DATE", (60, y_pos), yellow)
        _blit(surface, ctx, "normal", "UV INDEX", (280, y_pos), yellow)
        _blit(surface, ctx, "normal", "PROTECTION", (450, y_pos), yellow)
        y_pos += 40

        pygame.draw.line(surface, yellow, (50, y_pos - 5), (590, y_pos - 5), 1)

        for row in rows[:_MAX_ROWS]:
            date_text = _format_date(row.get("date"))
            uv_value = row.get("uv_index")
            if uv_value is None:
                continue
            try:
                level = self._protection(ctx, uv_value)
                _blit(surface, ctx, "normal", date_text, (60, y_pos), white)
                _blit(surface, ctx, "normal", f"{int(uv_value)}", (300, y_pos), white)
                _blit(surface, ctx, "normal", level, (460, y_pos), white)
            except (TypeError, ValueError):
                continue
            y_pos += 30

    @staticmethod
    def _protection(ctx: Any, uv_value: float) -> str:
        try:
            uv_ds = ctx.data.get("uv_index")
        except Exception:
            uv_ds = None
        if uv_ds is not None and callable(getattr(uv_ds, "protection_level", None)):
            return uv_ds.protection_level(uv_value)
        if uv_value <= 2:
            return "Low"
        if uv_value <= 5:
            return "Moderate"
        if uv_value <= 7:
            return "High"
        if uv_value <= 10:
            return "Very High"
        return "Extreme"

    @staticmethod
    def _daily_rows(ctx: Any) -> list[dict]:
        try:
            uv_ds = ctx.data.get("uv_index")
            location = ctx.location
            if uv_ds is None or location is None:
                return []
            daily = uv_ds.daily(location.lat, location.lon)
        except Exception:
            return []
        return daily or []
