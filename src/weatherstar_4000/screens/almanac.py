"""Weather Almanac screen: statistics for the day plus sun & moon."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen


@plugin
class AlmanacScreen(Screen):
    name = "almanac"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    layout = (
        ComponentSpec(component="background", config={"background_name": "4"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Weather", "title_bottom": "Almanac", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        current = self.weather_data(ctx, "get_current") or {}
        white = self.color(ctx, "white")
        yellow = self.color(ctx, "yellow")

        date_str = datetime.now().strftime("%B %d, %Y")
        date_surf = self.font(ctx, "normal").render(
            f"Weather Statistics for {date_str}", True, yellow
        )
        surface.blit(date_surf, date_surf.get_rect(center=(320, 100)))

        y_pos = 130
        stats_title = self.font(ctx, "extended").render("CURRENT CONDITIONS", True, yellow)
        surface.blit(stats_title, (60, y_pos))
        y_pos += 35

        temp_f = self.fahrenheit(self.num(current, "temperature"))
        if temp_f is not None:
            row = self.font(ctx, "normal").render(
                f"Temperature: {temp_f}\N{DEGREE SIGN}F", True, white
            )
            surface.blit(row, (80, y_pos))
            y_pos += 25

        humidity = self.num(current, "relativeHumidity")
        if humidity is not None:
            row = self.font(ctx, "normal").render(f"Humidity: {humidity:.0f}%", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 25

        dewpoint_f = self.fahrenheit(self.num(current, "dewpoint"))
        if dewpoint_f is not None:
            row = self.font(ctx, "normal").render(
                f"Dewpoint: {dewpoint_f}\N{DEGREE SIGN}F", True, white
            )
            surface.blit(row, (80, y_pos))
            y_pos += 25

        pressure_value = self.num(current, "barometricPressure")
        if pressure_value is None:
            pressure_value = self.num(current, "pressure")
        if pressure_value is not None:
            pressure_inhg = pressure_value * 0.00029530
            row = self.font(ctx, "normal").render(f"Pressure: {pressure_inhg:.2f} in", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 25

        visibility = self.num(current, "visibility")
        if visibility is not None:
            vis_miles = visibility / 1609.34
            row = self.font(ctx, "normal").render(f"Visibility: {vis_miles:.1f} miles", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 35

        y_pos += 10
        sun_title = self.font(ctx, "extended").render("SUN & MOON", True, yellow)
        surface.blit(sun_title, (60, y_pos))
        y_pos += 35

        sunrise_surf = self.font(ctx, "normal").render("Sunrise: 6:45 AM", True, white)
        surface.blit(sunrise_surf, (80, y_pos))
        y_pos += 25

        sunset_surf = self.font(ctx, "normal").render("Sunset: 7:30 PM", True, white)
        surface.blit(sunset_surf, (80, y_pos))
        y_pos += 25

        moon_surf = self.font(ctx, "normal").render("Moon Phase: Waxing Gibbous", True, white)
        surface.blit(moon_surf, (80, y_pos))
