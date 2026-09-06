"""Regional Observations screen: station, temperature, wind and obs time."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.datasources.noaa import CurrentConditions
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen


@plugin
class RegionalObservationsScreen(Screen):
    name = "regional_observations"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    layout = (
        ComponentSpec(component="background", config={"background_name": "5"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Latest", "title_bottom": "Observations", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        current: CurrentConditions | None = self.weather_data(ctx, "get_current")
        if current is None:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        white = self.color(ctx, "white")
        yellow = self.color(ctx, "yellow")
        y_pos = 120

        station = current.station or "Station"
        station_surf = self.font(ctx, "normal").render(f"Station: {station}", True, yellow)
        surface.blit(station_surf, (60, y_pos))
        y_pos += 40

        temp_f = current.temperature_f
        if temp_f is not None:
            temp_surf = self.font(ctx, "normal").render(
                f"Temperature: {temp_f}\N{DEGREE SIGN}", True, white
            )
            surface.blit(temp_surf, (60, y_pos))
            y_pos += 30

        wind_mph = current.wind_mph
        if wind_mph is not None:
            wind_surf = self.font(ctx, "normal").render(f"Wind: {wind_mph} mph", True, white)
            surface.blit(wind_surf, (60, y_pos))
            y_pos += 30

        timestamp = current.timestamp
        if timestamp:
            try:
                obs_time = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                time_str = obs_time.strftime("%I:%M %p %m/%d").lstrip("0")
                time_surf = self.font(ctx, "normal").render(f"Observed: {time_str}", True, white)
                surface.blit(time_surf, (60, y_pos))
            except (ValueError, TypeError):
                pass
