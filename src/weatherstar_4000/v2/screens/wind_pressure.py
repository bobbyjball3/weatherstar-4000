"""Wind & Pressure screen (port of legacy ``draw_wind_pressure``).

Reads the NOAA current-conditions properties (wind, gust, wind chill/heat
index, pressure) and shows a simulated steady trend arrow.
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

_WHITE = (255, 255, 255)
_YELLOW = (255, 255, 0)
_SOFT_RED = (255, 100, 100)

# m/s -> mph
_MS_TO_MPH = 2.23694
# Pa -> inches of mercury
_PA_TO_INHG = 0.00029530

_CARDINALS = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]


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


def _measure(current: dict, *keys: str) -> float | None:
    """Return the first present ``value`` for any of ``keys`` (dict or scalar)."""
    for key in keys:
        raw = current.get(key)
        if raw is None:
            continue
        if isinstance(raw, dict):
            value = raw.get("value")
        else:
            value = raw
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return None


def _cardinal(degrees: float) -> str:
    index = int((degrees + 11.25) / 22.5) % 16
    return _CARDINALS[index]


@plugin
class WindPressureScreen(Screen):
    name = "wind_pressure"
    media = ("backgrounds",)
    datasources = ("weather",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "1")
        render.draw_header(surface, ctx, "Wind &", "Pressure")

        colors = ctx.colors
        yellow = colors.get("yellow", _YELLOW)
        white = colors.get("white", _WHITE)

        current = self._current_conditions(ctx)
        if not current:
            render.draw_centered_text(surface, ctx, "Current conditions unavailable", 240)
            return

        y_pos = 120
        _blit(surface, ctx, "extended", "WIND CONDITIONS", (60, y_pos), yellow)
        y_pos += 35

        wind_speed = _measure(current, "windSpeed")
        wind_dir = _measure(current, "windDirection")
        wind_gust = _measure(current, "windGust")

        if wind_speed is not None:
            wind_mph = int(wind_speed * _MS_TO_MPH)
            _blit(surface, ctx, "normal", f"Speed: {wind_mph} mph", (80, y_pos), white)
            y_pos += 30

        if wind_dir is not None:
            dir_text = _cardinal(wind_dir)
            _blit(
                surface,
                ctx,
                "normal",
                f"Direction: {dir_text} ({wind_dir:.0f}\u00b0)",
                (80, y_pos),
                white,
            )
            y_pos += 30

        if wind_gust is not None:
            gust_mph = int(wind_gust * _MS_TO_MPH)
            _blit(surface, ctx, "normal", f"Gusts: {gust_mph} mph", (80, y_pos), yellow)
            y_pos += 30

        wind_chill = _measure(current, "windChill")
        heat_index = _measure(current, "heatIndex")
        if wind_chill is not None:
            wc_f = int(wind_chill * 9 / 5 + 32)
            blue = colors.get("blue", (128, 128, 255))
            _blit(surface, ctx, "normal", f"Wind Chill: {wc_f}\u00b0F", (80, y_pos), blue)
            y_pos += 30
        elif heat_index is not None:
            hi_f = int(heat_index * 9 / 5 + 32)
            _blit(surface, ctx, "normal", f"Heat Index: {hi_f}\u00b0F", (80, y_pos), _SOFT_RED)
            y_pos += 30

        y_pos += 20
        _blit(surface, ctx, "extended", "BAROMETRIC PRESSURE", (60, y_pos), yellow)
        y_pos += 35

        pressure = _measure(current, "pressure", "barometricPressure")
        if pressure is not None:
            pressure_inhg = pressure * _PA_TO_INHG
            _blit(
                surface,
                ctx,
                "normal",
                f"Current: {pressure_inhg:.2f} in",
                (80, y_pos),
                white,
            )
            y_pos += 30

            font_normal = _font(ctx, "normal")
            if font_normal is not None:
                trend = font_normal.render("Trend: Steady", True, white)
                surface.blit(trend, (80, y_pos))
                arrow_x = 80 + trend.get_width() + 14
                pygame.draw.polygon(
                    surface,
                    white,
                    [(arrow_x + 10, y_pos + 12), (arrow_x, y_pos + 4), (arrow_x, y_pos + 20)],
                )

    @staticmethod
    def _current_conditions(ctx: Any) -> dict:
        try:
            weather = ctx.data.get("weather")
            location = ctx.location
            if weather is None or location is None:
                return {}
            current = weather.get_current(location.lat, location.lon)
        except Exception:
            return {}
        return current or {}
