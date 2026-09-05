"""Local Forecast screen: three-day column layout with wrapped text."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

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


def _wrap_lines(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    for word in (text or "").split():
        test_line = " ".join(current + [word])
        if font.size(test_line)[0] > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


@plugin
class LocalForecastScreen(Screen):
    name = "local_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        _ensure_fonts(ctx)
        render.draw_background(surface, ctx, "2")
        render.draw_header(surface, ctx, "Local", "Forecast", has_noaa=True)

        forecast = _data(ctx, "get_forecast") or {}
        try:
            periods = forecast.get("periods") or []
        except Exception:
            periods = []

        if len(periods) < 3:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        yellow = _color(ctx, "yellow")
        white = _color(ctx, "white")
        total_width = 640
        col_width = 180
        col_spacing = 30
        total_cols_width = (col_width * 3) + (col_spacing * 2)
        start_x = (total_width - total_cols_width) // 2
        columns = [
            start_x + 10,
            start_x + col_width + col_spacing,
            start_x + (col_width + col_spacing) * 2 - 10,
        ]

        for col_idx, period in enumerate(periods[:3]):
            col_x = columns[col_idx]
            center_x = col_x + col_width // 2
            name = str(period.get("name", ""))

            if col_idx == 0:
                if "Tonight" in name or "Overnight" in name or "Night" in name.split()[-1]:
                    display_name = "TONIGHT"
                else:
                    display_name = "TODAY"
            elif col_idx == 1:
                display_name = "TOMORROW"
            else:
                day_name = (
                    name.replace(" Night", "").replace(" Afternoon", "").replace(" Morning", "")
                )
                display_name = day_name.upper()[:9]

            name_surf = _font(ctx, "extended").render(display_name, True, yellow)
            surface.blit(name_surf, name_surf.get_rect(center=(center_x, 120)))

            temp = period.get("temperature")
            if temp is not None:
                temp_surf = _font(ctx, "normal").render(f"{temp}\N{DEGREE SIGN}", True, white)
                surface.blit(temp_surf, temp_surf.get_rect(center=(center_x, 150)))

            try:
                detailed = period.get("detailedForecast") or ""
            except Exception:
                detailed = ""
            lines = _wrap_lines(_font(ctx, "forecast"), str(detailed), col_width - 20)

            y_pos = 180
            for line in lines[:10]:
                text_surf = _font(ctx, "forecast").render(line, True, white)
                surface.blit(text_surf, text_surf.get_rect(center=(center_x, y_pos)))
                y_pos += 18
