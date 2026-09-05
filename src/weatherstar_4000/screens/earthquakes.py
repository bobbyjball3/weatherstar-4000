"""Recent Earthquakes screen: USGS rows from the earthquakes datasource."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen

_MAX_ROWS = 8

_ORANGE = (255, 140, 0)
_RED = (255, 0, 0)


@plugin
class EarthquakesScreen(Screen):
    name = "earthquakes"
    media = ("backgrounds", "fonts", "logos")
    datasources = ("earthquakes",)

    @staticmethod
    def _mag_color(magnitude: float) -> tuple[int, int, int]:
        if magnitude >= 6.0:
            return _RED
        if magnitude >= 5.0:
            return _ORANGE
        if magnitude >= 4.0:
            return (255, 255, 0)
        return (255, 255, 255)

    layout = (
        ComponentSpec(component="background", config={"background_name": "5"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Recent", "title_bottom": "Earthquakes", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    @staticmethod
    def _format_time(time_ms: Any) -> str:
        try:
            epoch = float(time_ms) / 1000.0
            return datetime.utcfromtimestamp(epoch).strftime("%m/%d %H:%M")
        except Exception:  # noqa: BLE001 - unparseable timestamp
            return ""

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        lat, lon = self.latlon(ctx)
        quakes: list[dict] = []
        ds = self.datasource(ctx, "earthquakes")
        if ds is not None:
            try:
                quakes = list(ds.recent(lat, lon) or [])
            except Exception:  # noqa: BLE001 - data is optional
                quakes = []

        if not quakes:
            message = self.font(ctx, "normal").render(
                "Earthquake data unavailable", True, self.color(ctx, "white", (255, 255, 255))
            )
            surface.blit(message, message.get_rect(center=(320, 240)))
            return

        yellow = self.color(ctx, "yellow", (255, 255, 0))
        white = self.color(ctx, "white", (255, 255, 255))
        normal = self.font(ctx, "normal")
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
                time_display = self._format_time(quake.get("time"))

                mag_text = normal.render(f"{magnitude:.1f}", True, self._mag_color(magnitude))
                place_text = normal.render(place, True, white)
                time_text = normal.render(time_display, True, white)

                surface.blit(mag_text, (70, y_pos))
                surface.blit(place_text, (160, y_pos))
                surface.blit(time_text, (490, y_pos))
                y_pos += 28
            except Exception:  # noqa: BLE001 - skip malformed row
                continue
