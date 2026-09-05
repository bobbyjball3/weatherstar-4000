"""Weather Almanac screen: statistics for the day plus sun & moon."""

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


def _num(props: Any, key: str) -> float | None:
    try:
        return (props or {}).get(key, {}).get("value")
    except Exception:
        return None


def _fahrenheit(celsius: float | None) -> int | None:
    if celsius is None:
        return None
    try:
        return int(celsius * 9 / 5 + 32)
    except Exception:
        return None


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
class AlmanacScreen(Screen):
    name = "almanac"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        _ensure_fonts(ctx)
        render.draw_background(surface, ctx, "4")
        render.draw_header(surface, ctx, "Weather", "Almanac")

        current = _data(ctx, "get_current") or {}
        white = _color(ctx, "white")
        yellow = _color(ctx, "yellow")

        date_str = datetime.now().strftime("%B %d, %Y")
        date_surf = _font(ctx, "normal").render(f"Weather Statistics for {date_str}", True, yellow)
        surface.blit(date_surf, date_surf.get_rect(center=(320, 100)))

        y_pos = 130
        stats_title = _font(ctx, "extended").render("CURRENT CONDITIONS", True, yellow)
        surface.blit(stats_title, (60, y_pos))
        y_pos += 35

        temp_f = _fahrenheit(_num(current, "temperature"))
        if temp_f is not None:
            row = _font(ctx, "normal").render(f"Temperature: {temp_f}\N{DEGREE SIGN}F", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 25

        humidity = _num(current, "relativeHumidity")
        if humidity is not None:
            row = _font(ctx, "normal").render(f"Humidity: {humidity:.0f}%", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 25

        dewpoint_f = _fahrenheit(_num(current, "dewpoint"))
        if dewpoint_f is not None:
            row = _font(ctx, "normal").render(
                f"Dewpoint: {dewpoint_f}\N{DEGREE SIGN}F", True, white
            )
            surface.blit(row, (80, y_pos))
            y_pos += 25

        pressure_value = _num(current, "barometricPressure")
        if pressure_value is None:
            pressure_value = _num(current, "pressure")
        if pressure_value is not None:
            pressure_inhg = pressure_value * 0.00029530
            row = _font(ctx, "normal").render(f"Pressure: {pressure_inhg:.2f} in", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 25

        visibility = _num(current, "visibility")
        if visibility is not None:
            vis_miles = visibility / 1609.34
            row = _font(ctx, "normal").render(f"Visibility: {vis_miles:.1f} miles", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 35

        y_pos += 10
        sun_title = _font(ctx, "extended").render("SUN & MOON", True, yellow)
        surface.blit(sun_title, (60, y_pos))
        y_pos += 35

        sunrise_surf = _font(ctx, "normal").render("Sunrise: 6:45 AM", True, white)
        surface.blit(sunrise_surf, (80, y_pos))
        y_pos += 25

        sunset_surf = _font(ctx, "normal").render("Sunset: 7:30 PM", True, white)
        surface.blit(sunset_surf, (80, y_pos))
        y_pos += 25

        moon_surf = _font(ctx, "normal").render("Moon Phase: Waxing Gibbous", True, white)
        surface.blit(moon_surf, (80, y_pos))
