"""30-Day Precipitation History screen (port of legacy ``draw_precipitation_history``).

Shows a DATE / AMOUNT / STATUS table that scrolls in classic WeatherStar
row-jump style when more than eight rows are present.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

_WHITE = (255, 255, 255)
_YELLOW = (255, 255, 0)

_MAX_ROWS = 8


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


def _amount_status(precip: float) -> tuple[str, str]:
    if precip == 0:
        return "Trace", "Dry"
    if precip < 0.1:
        return f'{precip:.2f}"', "Light"
    if precip < 0.5:
        return f'{precip:.2f}"', "Moderate"
    return f'{precip:.2f}"', "Heavy"


@plugin
class PrecipitationHistoryScreen(Screen):
    name = "precipitation_history"
    media = ("backgrounds",)
    datasources = ("history",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "5")
        render.draw_header(surface, ctx, "30-Day", "Precipitation")

        colors = ctx.colors
        yellow = colors.get("yellow", _YELLOW)
        white = colors.get("white", _WHITE)

        history, rows = self._rows(ctx)
        if not rows:
            render.draw_centered_text(surface, ctx, "History data unavailable", 240)
            return

        y_pos = 120
        _blit(surface, ctx, "normal", "DATE", (60, y_pos), yellow)
        _blit(surface, ctx, "normal", "AMOUNT", (300, y_pos), yellow)
        _blit(surface, ctx, "normal", "STATUS", (480, y_pos), yellow)
        y_pos += 40

        pygame.draw.line(surface, yellow, (50, y_pos - 5), (590, y_pos - 5), 1)

        start_index = self._start_index(history, rows)
        for date_str, precip in rows[start_index : start_index + _MAX_ROWS]:
            date_display = _format_date(date_str)
            try:
                amount_display, status = _amount_status(float(precip))
            except (TypeError, ValueError):
                continue
            _blit(surface, ctx, "normal", date_display, (60, y_pos), white)
            _blit(surface, ctx, "normal", amount_display, (310, y_pos), white)
            _blit(surface, ctx, "normal", status, (490, y_pos), white)
            y_pos += 30

        if len(rows) > _MAX_ROWS:
            self._advance_scroll(history)

    @staticmethod
    def _rows(ctx: Any) -> tuple[Any, list[tuple]]:
        try:
            history = ctx.data.get("history")
            location = ctx.location
            if history is None or location is None:
                return None, []
            rows = history.precipitation(location.lat, location.lon)
        except Exception:
            return None, []
        return history, list(rows or [])

    @staticmethod
    def _start_index(history: Any, rows: list[tuple]) -> int:
        extra = len(rows) - _MAX_ROWS
        if extra <= 0:
            return 0
        try:
            offset = float(history.scroll_offsets[1])
        except Exception:
            offset = 0.0
        return (int(offset / 30.0)) % (extra + 1)

    @staticmethod
    def _advance_scroll(history: Any) -> None:
        try:
            history.scroll(time.time())
        except Exception:
            pass
