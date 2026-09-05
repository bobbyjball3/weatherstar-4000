"""Recent Earthquakes screen: USGS rows from the earthquakes datasource."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

_MAX_ROWS = 8

_ORANGE = (255, 140, 0)
_RED = (255, 0, 0)


def _font(ctx: Any, name: str, size: int) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None) or {}
    return fonts.get(name) or pygame.font.Font(None, size)


def _color(ctx: Any, key: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
    colors = getattr(ctx, "colors", None) or {}
    return colors.get(key, default)


def _ds(ctx: Any, name: str) -> Any:
    data = getattr(ctx, "data", None)
    if data is None:
        return None
    try:
        return data.get(name)
    except Exception:  # noqa: BLE001 - optional datasource
        return None


def _latlon(ctx: Any) -> tuple[float, float]:
    location = getattr(ctx, "location", None)
    if location is None:
        return 0.0, 0.0
    return float(getattr(location, "lat", 0.0)), float(getattr(location, "lon", 0.0))


def _mag_color(magnitude: float) -> tuple[int, int, int]:
    if magnitude >= 6.0:
        return _RED
    if magnitude >= 5.0:
        return _ORANGE
    if magnitude >= 4.0:
        return (255, 255, 0)
    return (255, 255, 255)


def _format_time(time_ms: Any) -> str:
    try:
        epoch = float(time_ms) / 1000.0
        return datetime.utcfromtimestamp(epoch).strftime("%m/%d %H:%M")
    except Exception:  # noqa: BLE001 - unparseable timestamp
        return ""


@plugin
class EarthquakesScreen(Screen):
    name = "earthquakes"
    media = ("backgrounds", "fonts", "logos")
    datasources = ("earthquakes",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "5")
        render.draw_header(surface, ctx, "Recent", "Earthquakes")

        lat, lon = _latlon(ctx)
        quakes: list[dict] = []
        ds = _ds(ctx, "earthquakes")
        if ds is not None:
            try:
                quakes = list(ds.recent(lat, lon) or [])
            except Exception:  # noqa: BLE001 - data is optional
                quakes = []

        if not quakes:
            message = _font(ctx, "normal", 20).render(
                "Earthquake data unavailable", True, _color(ctx, "white", (255, 255, 255))
            )
            surface.blit(message, message.get_rect(center=(320, 240)))
            return

        yellow = _color(ctx, "yellow", (255, 255, 0))
        white = _color(ctx, "white", (255, 255, 255))
        normal = _font(ctx, "normal", 20)
        y_pos = 120

        headers = ("MAG", "LOCATION", "TIME")
        positions = (60, 160, 480)
        for header, x in zip(headers, positions):
            surface.blit(normal.render(header, True, yellow), (x, y_pos))

        y_pos += 40
        pygame.draw.line(surface, yellow, (50, y_pos - 5), (590, y_pos - 5), 1)

        for quake in quakes[:_MAX_ROWS]:
            try:
                magnitude = float(quake.get("magnitude") or 0)
                place = str(quake.get("place") or "Unknown")[:25]
                time_display = _format_time(quake.get("time"))

                mag_text = normal.render(f"{magnitude:.1f}", True, _mag_color(magnitude))
                place_text = normal.render(place, True, white)
                time_text = normal.render(time_display, True, white)

                surface.blit(mag_text, (70, y_pos))
                surface.blit(place_text, (160, y_pos))
                surface.blit(time_text, (490, y_pos))
                y_pos += 28
            except Exception:  # noqa: BLE001 - skip malformed row
                continue
