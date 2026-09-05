"""Hourly Forecast screen: continuously scrolling hour-by-hour listing."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

_FONT_SIZES = {
    "title": 32,
    "large": 32,
    "extended": 32,
    "small": 28,
    "normal": 20,
    "forecast": 24,
    "tiny": 16,
    "scroller": 24,
}


def _ensure_fonts(ctx: Any) -> None:
    fonts = getattr(ctx, "fonts", None)
    if not isinstance(fonts, dict):
        return
    for name, size in _FONT_SIZES.items():
        fonts.setdefault(name, pygame.font.Font(None, size))


def _font(ctx: Any, name: str) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None)
    if isinstance(fonts, dict):
        found = fonts.get(name)
        if found is not None:
            return found
    return pygame.font.Font(None, _FONT_SIZES.get(name, 20))


def _color(
    ctx: Any, key: str, fallback: tuple[int, int, int] = (255, 255, 255)
) -> tuple[int, int, int]:
    try:
        return (ctx.colors or {}).get(key, fallback)
    except Exception:
        return fallback


def _weather(ctx: Any) -> Any:
    try:
        return ctx.data.get("weather")
    except Exception:
        return None


def _data(ctx: Any, method: str) -> Any:
    ds = _weather(ctx)
    if ds is None:
        return None
    fn = getattr(ds, method, None)
    loc = getattr(ctx, "location", None)
    if fn is None or loc is None:
        return None
    try:
        return fn(loc.lat, loc.lon)
    except Exception:
        return None


@plugin
class HourlyForecastScreen(Screen):
    name = "hourly_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        _ensure_fonts(ctx)
        render.draw_background(surface, ctx, "4")
        render.draw_header(surface, ctx, "Hourly", "Forecast")

        hourly = _data(ctx, "get_hourly") or {}
        try:
            periods = hourly.get("periods") or []
        except Exception:
            periods = []
        if not periods:
            forecast = _data(ctx, "get_forecast") or {}
            try:
                periods = forecast.get("periods") or []
            except Exception:
                periods = []

        yellow = _color(ctx, "yellow")
        white = _color(ctx, "white")

        if not periods:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        content_top = 125
        content_height = 265
        line_height = 25
        total_lines = len(periods[:24])
        total_content_height = total_lines * line_height

        scroll_time = pygame.time.get_ticks() // 50
        scroll_offset = scroll_time % (total_content_height + content_height)

        header_surf = _font(ctx, "small").render("TIME  TEMP  CONDITIONS", True, yellow)
        surface.blit(header_surf, (65, content_top))

        clip_rect = pygame.Rect(0, content_top + 30, 640, content_height)
        surface.set_clip(clip_rect)

        base_y = content_top + 30 + content_height - scroll_offset
        for loop in range(2):
            y_offset = loop * total_content_height
            for i, period in enumerate(periods[:24]):
                y_pos = base_y + y_offset + (i * line_height)
                if content_top <= y_pos <= content_top + content_height + 50:
                    start_time = period.get("startTime")
                    time_display = ""
                    if start_time:
                        try:
                            hour_time = datetime.fromisoformat(
                                str(start_time).replace("Z", "+00:00")
                            )
                            time_display = hour_time.strftime("%I %p").lstrip("0").rjust(7)
                        except (ValueError, TypeError):
                            time_display = ""
                    if not time_display:
                        time_display = str(period.get("name", ""))[:7].rjust(7)

                    temp = period.get("temperature")
                    if temp is None:
                        temp = 0
                    temp_display = f"{int(temp):3}\N{DEGREE SIGN}"

                    short = str(period.get("shortForecast", ""))[:35]
                    text = f"{time_display:6}{temp_display:5}{short}"
                    period_surf = _font(ctx, "normal").render(text, True, white)
                    surface.blit(period_surf, (65, y_pos))

        surface.set_clip(None)
