"""Regional Observations screen: station, temperature, wind and obs time."""

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


def _station_name(current: Any) -> str:
    station = ""
    try:
        station = str(current.get("station", "") or "")
    except Exception:
        station = ""
    if not station:
        return "Station"
    if "/stations/" in station:
        station = station.split("/stations/", 1)[1]
    else:
        station = station.rstrip("/").split("/")[-1]
    return station or "Station"


@plugin
class RegionalObservationsScreen(Screen):
    name = "regional_observations"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        _ensure_fonts(ctx)
        render.draw_background(surface, ctx, "5")
        render.draw_header(surface, ctx, "Latest", "Observations")

        current = _data(ctx, "get_current") or {}
        if not current:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        white = _color(ctx, "white")
        yellow = _color(ctx, "yellow")
        y_pos = 120

        station_surf = _font(ctx, "normal").render(
            f"Station: {_station_name(current)}", True, yellow
        )
        surface.blit(station_surf, (60, y_pos))
        y_pos += 40

        temp_f = _fahrenheit(_num(current, "temperature"))
        if temp_f is not None:
            temp_surf = _font(ctx, "normal").render(
                f"Temperature: {temp_f}\N{DEGREE SIGN}", True, white
            )
            surface.blit(temp_surf, (60, y_pos))
            y_pos += 30

        wind_speed = _num(current, "windSpeed")
        if wind_speed is not None:
            wind_mph = int(wind_speed * 0.621371)
            wind_surf = _font(ctx, "normal").render(f"Wind: {wind_mph} mph", True, white)
            surface.blit(wind_surf, (60, y_pos))
            y_pos += 30

        timestamp = ""
        try:
            timestamp = current.get("timestamp")
        except Exception:
            timestamp = None
        if timestamp:
            try:
                obs_time = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                time_str = obs_time.strftime("%I:%M %p %m/%d").lstrip("0")
                time_surf = _font(ctx, "normal").render(f"Observed: {time_str}", True, white)
                surface.blit(time_surf, (60, y_pos))
            except (ValueError, TypeError):
                pass
