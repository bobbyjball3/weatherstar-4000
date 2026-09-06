"""Recent Earthquakes screen: USGS rows from the earthquakes datasource."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar.components.base import ComponentSpec
from weatherstar.datasources.feeds import Earthquake
from weatherstar.registry import plugin
from weatherstar.screens.base import Screen
from weatherstar.themes import LayoutVariant

_MAX_ROWS = 8

_ORANGE = (255, 140, 0)
_RED = (255, 0, 0)


@plugin
class EarthquakesScreen(Screen):
    name = "earthquakes"
    media = ("backgrounds", "fonts", "logos")
    datasources = ("earthquakes",)

    variants = {
        LayoutVariant.WS4000: "compose_4000",
    }

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
    def _format_time(quake: Earthquake) -> str:
        if quake.time is None:
            return ""
        return quake.time.strftime("%m/%d %H:%M")

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        lat, lon = self.latlon(ctx)
        quakes: list[Earthquake] = []
        ds = self.datasource(ctx, "earthquakes")
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
            magnitude = quake.magnitude or 0.0
            place = quake.place[:25] or "Unknown"
            time_display = self._format_time(quake)

            mag_text = normal.render(f"{magnitude:.1f}", True, self._mag_color(magnitude))
            place_text = normal.render(place, True, white)
            time_text = normal.render(time_display, True, white)

            surface.blit(mag_text, (70, y_pos))
            surface.blit(place_text, (160, y_pos))
            surface.blit(time_text, (490, y_pos))
            y_pos += 28
