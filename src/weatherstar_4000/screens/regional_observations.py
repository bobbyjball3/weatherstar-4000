"""Regional Observations screen: station, temperature, wind and obs time."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
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

    @staticmethod
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

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        current = self.weather_data(ctx, "get_current") or {}
        if not current:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        white = self.color(ctx, "white")
        yellow = self.color(ctx, "yellow")
        y_pos = 120

        station_surf = self.font(ctx, "normal").render(
            f"Station: {self._station_name(current)}", True, yellow
        )
        surface.blit(station_surf, (60, y_pos))
        y_pos += 40

        temp_f = self.fahrenheit(self.num(current, "temperature"))
        if temp_f is not None:
            temp_surf = self.font(ctx, "normal").render(
                f"Temperature: {temp_f}\N{DEGREE SIGN}", True, white
            )
            surface.blit(temp_surf, (60, y_pos))
            y_pos += 30

        wind_speed = self.num(current, "windSpeed")
        if wind_speed is not None:
            wind_mph = int(wind_speed * 0.621371)
            wind_surf = self.font(ctx, "normal").render(f"Wind: {wind_mph} mph", True, white)
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
                time_surf = self.font(ctx, "normal").render(f"Observed: {time_str}", True, white)
                surface.blit(time_surf, (60, y_pos))
            except (ValueError, TypeError):
                pass
